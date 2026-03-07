import asyncio
import os
import re
import unicodedata

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
from academiaserver.config import (
    AI_CLOUD_ALLOW_SENSITIVE,
    AI_ENABLE_CLOUD_FALLBACK,
    AI_HTTP_MAX_RETRIES,
    AI_HTTP_RETRY_DELAY_SECONDS,
    AI_MAX_RETRIES,
    AI_PROVIDER,
    AI_TIMEOUT_SECONDS,
    INBOX_DIR,
    LOG_DIR,
    OLLAMA_BASE_URL,
    OLLAMA_CHAT_MODEL,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_CHAT_MODEL,
    REMINDER_MAX_RETRIES,
    REMINDER_RETRY_DELAY_SECONDS,
    SCHEDULER_INTERVAL_SECONDS,
)
from academiaserver.core import save_idea
from academiaserver.logger import log_event
from academiaserver.scheduler.reminders_scheduler import (
    get_due_reminders,
    get_pending_reminders,
    mark_as_reminded,
)

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID_ENV = os.getenv("TELEGRAM_CHAT_ID")


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
    ensure_writable_dir(INBOX_DIR, "INBOX_DIR")
    ensure_writable_dir(LOG_DIR, "LOG_DIR")
    log_event(
        "bot_startup_validation_ok",
        inbox_dir=INBOX_DIR,
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Mitzlia conectado. Enviame una nota o recordatorio y lo guardare."
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


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if not text:
        await update.message.reply_text("No recibi texto para procesar.")
        return

    if is_pending_reminders_query(text):
        log_event("bot_pending_reminders_query_detected")
        pending = get_pending_reminders(limit=5)
        if not pending:
            await update.message.reply_text("No tienes recordatorios pendientes.")
            return

        lines = ["Tus recordatorios pendientes:"]
        for reminder in pending:
            dt = reminder.get("metadata", {}).get("datetime", "sin fecha")
            lines.append(f"- {dt}: {reminder.get('content', '')}")

        await update.message.reply_text("\n".join(lines))
        return

    try:
        orchestrator = context.application.bot_data.get("ai_orchestrator")
        if orchestrator is None:
            orchestrator = build_orchestrator()
            context.application.bot_data["ai_orchestrator"] = orchestrator

        note, reply_text = orchestrator.process_message(text, source="telegram")
        saved = save_idea(note)
        log_event(
            "bot_note_saved",
            note_id=saved.get("id"),
            note_type=saved.get("type"),
            source="telegram",
        )
        await update.message.reply_text(f"{reply_text}\nID: {saved['id']}")
    except Exception as exc:
        log_event("bot_note_save_error", level="ERROR", error=str(exc))
        await update.message.reply_text("Error al guardar la nota.")


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


async def scheduler_loop(application, chat_id: int):
    log_event("bot_scheduler_loop_started")
    while True:
        reminders = get_due_reminders()
        for reminder in reminders:
            reminder_id = reminder.get("id", "sin_id")
            message = f"Recordatorio:\n{reminder['content']}"
            sent = await send_reminder_with_retry(
                application,
                chat_id=chat_id,
                message=message,
                reminder_id=reminder_id,
            )
            if sent:
                mark_as_reminded(reminder)

        await asyncio.sleep(SCHEDULER_INTERVAL_SECONDS)


def main():
    validate_config()
    chat_id = get_chat_id()
    orchestrator = build_orchestrator()

    async def post_init(application):
        application.bot_data["ai_orchestrator"] = orchestrator
        application.create_task(scheduler_loop(application, chat_id))

    application = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    log_event("bot_polling_started")
    application.run_polling()


if __name__ == "__main__":
    main()
