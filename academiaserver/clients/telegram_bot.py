import asyncio
import os
import re
import tempfile
import unicodedata
from collections import deque
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from academiaserver.ai import AIOrchestrator, CloudProvider, HybridProvider, OllamaProvider
from academiaserver.ai.agent_router import AgentRouter
from academiaserver.ai.whisper_transcriber import WhisperTranscriber
from academiaserver.config import (
    AI_CLOUD_ALLOW_SENSITIVE,
    AI_ENABLE_CLOUD_FALLBACK,
    AI_HTTP_MAX_RETRIES,
    AI_HTTP_RETRY_DELAY_SECONDS,
    AI_MAX_RETRIES,
    AI_PROVIDER,
    AI_TIMEOUT_SECONDS,
    LOG_DIR,
    OLLAMA_BASE_URL,
    OLLAMA_CHAT_MODEL,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_CHAT_MODEL,
    OUTPUTS_DIR,
    TEMPLATES_DIR,
    REMINDER_MAX_RETRIES,
    REMINDER_RETRY_DELAY_SECONDS,
    SCHEDULER_INTERVAL_SECONDS,
    WHISPER_COMPUTE_TYPE,
    WHISPER_DEVICE,
    WHISPER_LANGUAGE,
    WHISPER_MODEL,
    WHISPER_TIMEOUT,
)
from academiaserver.document_gen.beamer import MarkdownToBeamer
from academiaserver.document_gen.writer import DocumentWriter
from academiaserver.core import find_related_notes, get_memory_context, save_idea
from academiaserver.logger import log_event
from academiaserver.scheduler.reminders_scheduler import get_pending_reminders

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID_ENV = os.getenv("TELEGRAM_CHAT_ID")

# Contexto conversacional por chat: últimos 5 turnos (user + assistant)
_chat_contexts: dict[int, deque] = {}

# Tarea educativa activa por chat — permite multi-turno sin WorkflowEngine
# Se llena cuando un agente devuelve missing_info != [] y se limpia al completar.
_active_educational_tasks: dict[int, str] = {}

# Límite seguro de Telegram (margen sobre los 4096 caracteres reales)
_TELEGRAM_MAX_CHARS = 4000

# Singleton del transcriptor de voz
_whisper = WhisperTranscriber(
    model_name=WHISPER_MODEL,
    language=WHISPER_LANGUAGE,
    device=WHISPER_DEVICE,
    compute_type=WHISPER_COMPUTE_TYPE,
    openai_api_key=OPENAI_API_KEY,
    openai_base_url=OPENAI_BASE_URL,
    timeout_seconds=WHISPER_TIMEOUT,
)


def get_chat_id() -> int:
    if not CHAT_ID_ENV:
        raise RuntimeError("Falta TELEGRAM_CHAT_ID en variables de entorno")
    try:
        return int(CHAT_ID_ENV)
    except ValueError as exc:
        raise RuntimeError("TELEGRAM_CHAT_ID debe ser un numero entero") from exc


def ensure_writable_dir(path: str, label: str):
    os.makedirs(path, exist_ok=True)
    if not os.access(path, os.W_OK):
        raise RuntimeError(f"El directorio {label} no tiene permisos de escritura: {path}")


def validate_config():
    if not TOKEN:
        raise RuntimeError("Falta TELEGRAM_TOKEN en variables de entorno")
    get_chat_id()
    ensure_writable_dir(LOG_DIR, "LOG_DIR")
    ensure_writable_dir(OUTPUTS_DIR, "OUTPUTS_DIR")
    # TEMPLATES_DIR es de solo lectura: solo advertir si no existe (no es crítico)
    if not Path(TEMPLATES_DIR).exists():
        log_event("bot_templates_dir_missing", level="WARNING", path=TEMPLATES_DIR)
    log_event(
        "bot_startup_validation_ok",
        log_dir=LOG_DIR,
        scheduler_interval=SCHEDULER_INTERVAL_SECONDS,
        ai_provider=AI_PROVIDER,
    )


def build_orchestrator() -> AIOrchestrator:
    provider = None
    local_provider = OllamaProvider(
        base_url=OLLAMA_BASE_URL,
        chat_model=OLLAMA_CHAT_MODEL,
        timeout_seconds=AI_TIMEOUT_SECONDS,
        http_max_retries=AI_HTTP_MAX_RETRIES,
        http_retry_delay_seconds=AI_HTTP_RETRY_DELAY_SECONDS,
    )

    if AI_PROVIDER == "ollama":
        provider = local_provider
        log_event(
            "ai_provider_initialized",
            provider="ollama",
            model=OLLAMA_CHAT_MODEL,
            base_url=OLLAMA_BASE_URL,
        )
    elif AI_PROVIDER == "cloud":
        provider = CloudProvider(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL,
            chat_model=OPENAI_CHAT_MODEL,
            timeout_seconds=AI_TIMEOUT_SECONDS,
            http_max_retries=AI_HTTP_MAX_RETRIES,
            http_retry_delay_seconds=AI_HTTP_RETRY_DELAY_SECONDS,
        )
        log_event(
            "ai_provider_initialized",
            provider="cloud",
            model=OPENAI_CHAT_MODEL,
            base_url=OPENAI_BASE_URL,
        )
    elif AI_PROVIDER == "hybrid":
        cloud_provider = None
        if OPENAI_API_KEY:
            cloud_provider = CloudProvider(
                api_key=OPENAI_API_KEY,
                base_url=OPENAI_BASE_URL,
                chat_model=OPENAI_CHAT_MODEL,
                timeout_seconds=AI_TIMEOUT_SECONDS,
                http_max_retries=AI_HTTP_MAX_RETRIES,
                http_retry_delay_seconds=AI_HTTP_RETRY_DELAY_SECONDS,
            )

        provider = HybridProvider(
            local_provider=local_provider,
            cloud_provider=cloud_provider,
            allow_cloud_fallback=AI_ENABLE_CLOUD_FALLBACK,
            allow_sensitive_to_cloud=AI_CLOUD_ALLOW_SENSITIVE,
        )
        log_event(
            "ai_provider_initialized",
            provider="hybrid",
            local_model=OLLAMA_CHAT_MODEL,
            cloud_model=OPENAI_CHAT_MODEL if OPENAI_API_KEY else "not_configured",
            cloud_fallback=AI_ENABLE_CLOUD_FALLBACK,
            allow_sensitive_to_cloud=AI_CLOUD_ALLOW_SENSITIVE,
        )
    else:
        log_event("ai_provider_initialized", provider="rules")

    return AIOrchestrator(provider=provider, ai_max_retries=AI_MAX_RETRIES)


async def _send_long_message(update: Update, text: str):
    """Envía un mensaje largo dividiéndolo en partes si supera el límite de Telegram."""
    if len(text) <= _TELEGRAM_MAX_CHARS:
        await update.message.reply_text(text)
        return
    # Divide en bloques respetando saltos de línea
    parts = []
    current = ""
    for line in text.splitlines(keepends=True):
        if len(current) + len(line) > _TELEGRAM_MAX_CHARS:
            if current:
                parts.append(current.rstrip())
            current = line
        else:
            current += line
    if current.strip():
        parts.append(current.rstrip())
    for part in parts:
        await update.message.reply_text(part)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Aquí, Profesor. Dígame — notas, ideas, recordatorios. Lo que necesite."
    )


def is_pending_reminders_query(text: str) -> bool:
    lowered = text.lower().strip()
    normalized = unicodedata.normalize("NFD", lowered)
    normalized = "".join(
        ch for ch in normalized if unicodedata.category(ch) != "Mn"
    )
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    normalized = " ".join(normalized.split())

    patterns = [
        "que recordatorios tengo pendientes",
        "recordatorios pendientes",
        "recordatorios tengo",
        "recordatorio pendiente",
        "recordatorios por hacer",
    ]
    return any(pattern in normalized for pattern in patterns)


async def _process_text(update: Update, text: str, context: ContextTypes.DEFAULT_TYPE):
    """Procesa texto (ya sea de mensaje directo o transcripción de voz)."""
    if is_pending_reminders_query(text):
        log_event("bot_pending_reminders_query_detected")
        pending = get_pending_reminders(limit=5)
        if not pending:
            await update.message.reply_text("Sin pendientes por ahora, Profesor.")
            return

        lines = ["Pendientes, Profesor:"]
        for reminder in pending:
            dt = reminder.get("metadata", {}).get("datetime", "sin fecha")
            titulo = reminder.get("title") or reminder.get("content", "")[:60]
            lines.append(f"- {dt}: {titulo}")

        await update.message.reply_text("\n".join(lines))
        return

    try:
        orchestrator = context.application.bot_data.get("ai_orchestrator")
        if orchestrator is None:
            orchestrator = build_orchestrator()
            context.application.bot_data["ai_orchestrator"] = orchestrator

        # Inicializar AgentRouter perezosamente (comparte provider con el orchestrator)
        agent_router = context.application.bot_data.get("agent_router")
        if agent_router is None:
            agent_router = AgentRouter(orchestrator.provider)
            context.application.bot_data["agent_router"] = agent_router

        chat_id = update.message.chat_id
        ctx = list(_chat_contexts.get(chat_id, []))

        # ── Routing educativo (Fase 4.2) ──────────────────────────────────────
        # Si hay una tarea activa (multi-turno) o el mensaje inicia una nueva,
        # desviar al agente especializado antes del orchestrator general.
        active_task = _active_educational_tasks.get(chat_id)
        task_type = active_task or agent_router.detect_task_type(text)

        if task_type:
            agent = agent_router.get_agent(task_type)
            if agent:
                memory = get_memory_context(text, top_k=3)
                note, reply_text = agent.process(text, context=ctx, memory=memory)
                missing_info = note.get("metadata", {}).get("missing_info", [])

                _chat_contexts.setdefault(chat_id, deque(maxlen=5)).append({
                    "user": text,
                    "assistant": reply_text or "",
                })

                if missing_info:
                    # Tarea incompleta: registrar tipo activo y preguntar por datos faltantes
                    _active_educational_tasks[chat_id] = task_type
                    log_event(
                        "bot_educational_task_pending",
                        task_type=task_type,
                        missing=missing_info,
                    )
                    await update.message.reply_text(reply_text)
                else:
                    # Tarea completa: limpiar estado, guardar nota y enviar archivo
                    _active_educational_tasks.pop(chat_id, None)
                    note["content"] = reply_text  # BD indexa el documento (para RAG)
                    saved = save_idea(note)
                    log_event(
                        "bot_educational_task_saved",
                        task_type=task_type,
                        note_id=saved.get("id"),
                        source="telegram",
                    )

                    title = note.get("title") or task_type
                    writer = DocumentWriter()
                    try:
                        md_path = writer.save_markdown(reply_text, task_type, title)
                        if task_type == "slides":
                            tex_content = MarkdownToBeamer().convert(reply_text, title=title)
                            tex_path = writer.save_tex(tex_content, task_type, title)
                            attachment_path = tex_path
                            attachment_name = tex_path.name
                        else:
                            attachment_path = md_path
                            attachment_name = md_path.name

                        with open(attachment_path, "rb") as fh:
                            await update.message.reply_document(
                                document=fh,
                                filename=attachment_name,
                                caption=f"📄 {task_type.capitalize()} guardada. ID: {saved['id']}",
                            )
                    except Exception as exc:
                        log_event("bot_document_send_error", level="WARNING", error=str(exc))
                        await _send_long_message(
                            update, f"{reply_text}\n\n📋 ID: {saved['id']}"
                        )
                return
        # ── Fin routing educativo ─────────────────────────────────────────────

        memory = get_memory_context(text, top_k=5)
        note, reply_text = orchestrator.process_message(
            text, source="telegram", context=ctx, memory=memory
        )
        _chat_contexts.setdefault(chat_id, deque(maxlen=5)).append({
            "user": text,
            "assistant": reply_text or "",
        })

        # Las preguntas no se guardan — se responden con síntesis de IA sobre el historial
        if note.get("type") == "pregunta":
            log_event("bot_question_handled", source="telegram")
            if reply_text and reply_text.strip():
                # La IA ya procesó el historial relevante y sintetizó la respuesta
                await update.message.reply_text(reply_text)
            elif memory:
                # Fallback si la IA no generó respuesta: listar notas relevantes
                lines = ["Lo que tengo registrado, Profesor:"]
                for m in memory[:3]:
                    fecha = (m.get("created_at") or "")[:10]
                    titulo = m.get("title") or m.get("content", "")[:60]
                    lines.append(f"- [{fecha}] {titulo}")
                await update.message.reply_text("\n".join(lines))
            else:
                await update.message.reply_text(
                    "No tengo nada registrado sobre eso, Profesor."
                )
            return

        saved = save_idea(note)
        log_event(
            "bot_note_saved",
            note_id=saved.get("id"),
            note_type=saved.get("type"),
            source="telegram",
        )

        # Conexiones automáticas — Fase 4
        # Busca notas existentes relacionadas semánticamente con la recién guardada.
        # Degradación suave: si falla (Ollama no disponible, sin embeddings), continúa normal.
        try:
            related = find_related_notes(text, exclude_id=saved.get("id"), top_k=2)
            if related:
                partes = []
                for r in related:
                    fecha = (r.get("created_at") or "")[:10]
                    titulo = r.get("title") or r.get("content", "")[:40]
                    partes.append(f"[{fecha}] {titulo}")
                if partes:
                    reply_text += "\n\n🔗 " + " · ".join(partes)
                    log_event(
                        "bot_connections_found",
                        note_id=saved.get("id"),
                        related_count=len(related),
                    )
        except Exception as exc:
            log_event("bot_connections_error", level="WARNING", error=str(exc))

        await update.message.reply_text(f"{reply_text}\nID: {saved['id']}")
    except Exception as exc:
        log_event("bot_note_save_error", level="ERROR", error=str(exc))
        await update.message.reply_text("Algo falló al guardar, Profesor. Intente de nuevo.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if not text:
        await update.message.reply_text("No recibí texto, Profesor.")
        return
    await _process_text(update, text, context)


async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if CHAT_ID_ENV and str(chat_id) != str(CHAT_ID_ENV):
        return

    await update.message.reply_text("Transcribiendo nota de voz, Profesor...")

    tg_file = await update.message.voice.get_file()
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        await tg_file.download_to_drive(tmp_path)
        text = _whisper.transcribe(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    if not text:
        log_event("bot_voice_transcription_failed", chat_id=chat_id)
        await update.message.reply_text(
            "No pude transcribir el audio, Profesor. ¿Puede enviarlo como texto?"
        )
        return

    log_event("bot_voice_transcribed", chars=len(text))
    await _process_text(update, text, context)


async def send_reminder_with_retry(application, chat_id: int, message: str, reminder_id: str):
    for attempt in range(1, REMINDER_MAX_RETRIES + 1):
        try:
            await application.bot.send_message(chat_id=chat_id, text=message)
            log_event(
                "bot_reminder_sent",
                reminder_id=reminder_id,
                attempt=attempt,
            )
            return True
        except Exception as exc:
            log_event(
                "bot_reminder_send_failed",
                level="WARNING",
                reminder_id=reminder_id,
                attempt=attempt,
                error=str(exc),
            )
            if attempt < REMINDER_MAX_RETRIES:
                await asyncio.sleep(REMINDER_RETRY_DELAY_SECONDS)

    log_event(
        "bot_reminder_send_exhausted",
        level="ERROR",
        reminder_id=reminder_id,
        max_retries=REMINDER_MAX_RETRIES,
    )
    return False


def main():
    validate_config()
    orchestrator = build_orchestrator()

    async def post_init(application):
        application.bot_data["ai_orchestrator"] = orchestrator
        application.bot_data["agent_router"] = AgentRouter(orchestrator.provider)

    application = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    application.add_handler(
        MessageHandler(filters.VOICE & ~filters.COMMAND, handle_voice_message)
    )

    log_event("bot_polling_started")
    application.run_polling()


if __name__ == "__main__":
    main()
