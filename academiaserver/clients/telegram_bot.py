import os
import re
import unicodedata
from collections import deque

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from academiaserver.ai.claude import ClaudeProvider
from academiaserver.config import TELEGRAM_CHAT_ID, TELEGRAM_TOKEN
from academiaserver.core import get_pending_reminders, save_idea
from academiaserver.db.database import init_db
from academiaserver.logger import log_event
from academiaserver.scheduler.reminders_scheduler import get_due_reminders

load_dotenv()

# Contexto conversacional: últimos 5 turnos por chat
_chat_contexts: dict[int, deque] = {}

_TELEGRAM_MAX_CHARS = 4000

_claude = ClaudeProvider()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_pending_query(text: str) -> bool:
    normalized = unicodedata.normalize("NFD", text.lower())
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized).split()
    normalized = " ".join(normalized)
    patterns = [
        "recordatorios pendientes",
        "que recordatorios tengo",
        "recordatorio pendiente",
        "recordatorios por hacer",
    ]
    return any(p in normalized for p in patterns)


async def _send(update: Update, text: str):
    """Envía mensaje dividiéndolo si supera el límite de Telegram."""
    if len(text) <= _TELEGRAM_MAX_CHARS:
        await update.message.reply_text(text)
        return
    parts, current = [], ""
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


# ── Handlers ──────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Aquí, Profesor. Dígame — notas, ideas, recordatorios."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if not text:
        await update.message.reply_text("No recibí texto, Profesor.")
        return

    chat_id = update.message.chat_id

    # Consulta de recordatorios pendientes
    if _is_pending_query(text):
        pending = get_pending_reminders(limit=5)
        if not pending:
            await update.message.reply_text("Sin pendientes por ahora, Profesor.")
            return
        lines = ["Pendientes, Profesor:"]
        for r in pending:
            dt = (r.get("reminder_datetime") or "sin fecha")[:16]
            titulo = r.get("title") or r.get("content", "")[:60]
            lines.append(f"- {dt}: {titulo}")
        await update.message.reply_text("\n".join(lines))
        return

    # Contexto conversacional
    ctx = list(_chat_contexts.get(chat_id, []))

    try:
        analysis = _claude.analyze(text, context=ctx)
    except Exception as exc:
        log_event("bot_claude_error", level="ERROR", error=str(exc))
        await update.message.reply_text("Algo falló con la IA, Profesor. Intente de nuevo.")
        return

    reply_text = analysis.get("reply_text") or "Anotado, Profesor."
    note_type = analysis.get("type", "nota")

    # Las preguntas no se guardan — solo se responde
    if note_type == "pregunta":
        _chat_contexts.setdefault(chat_id, deque(maxlen=5)).append(
            {"user": text, "assistant": reply_text}
        )
        log_event("bot_pregunta_respondida")
        await _send(update, reply_text)
        return

    # Construir nota y guardar
    note = {
        "content": text,
        "type": note_type,
        "title": analysis.get("title") or text[:60],
        "tags": analysis.get("tags") or [],
        "summary": analysis.get("summary") or "",
        "priority": analysis.get("priority") or "media",
        "source": "telegram",
    }
    if note_type == "recordatorio":
        note["reminder_datetime"] = analysis.get("reminder_datetime")
        note["reminded"] = False

    try:
        saved = save_idea(note)
    except Exception as exc:
        log_event("bot_save_error", level="ERROR", error=str(exc))
        await update.message.reply_text("No pude guardar la nota, Profesor. Intente de nuevo.")
        return

    _chat_contexts.setdefault(chat_id, deque(maxlen=5)).append(
        {"user": text, "assistant": reply_text}
    )

    log_event("bot_nota_guardada", id=saved["id"], type=note_type)
    await update.message.reply_text(f"{reply_text}\nID: {saved['id']}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not TELEGRAM_TOKEN:
        raise RuntimeError("Falta TELEGRAM_TOKEN en .env")
    if not TELEGRAM_CHAT_ID:
        raise RuntimeError("Falta TELEGRAM_CHAT_ID en .env")

    init_db()
    log_event("bot_iniciado")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Mitzlia activa. Esperando mensajes...")
    app.run_polling()


if __name__ == "__main__":
    main()
