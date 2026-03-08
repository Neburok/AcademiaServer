import time

import requests

from academiaserver.config import (
    REMINDER_MAX_RETRIES,
    REMINDER_RETRY_DELAY_SECONDS,
    SCHEDULER_INTERVAL_SECONDS,
    TELEGRAM_CHAT_ID,
    TELEGRAM_TOKEN,
)
from academiaserver.db import database as _db
from academiaserver.db import repository
from academiaserver.events.bus import bus
from academiaserver.logger import log_event


def get_due_reminders() -> list[dict]:
    db = _db.SessionLocal()
    try:
        reminders = repository.get_due_reminders(db)
        if reminders:
            log_event("scheduler_due_reminders_found", count=len(reminders))
        return reminders
    finally:
        db.close()


def get_pending_reminders(limit: int = 5) -> list[dict]:
    db = _db.SessionLocal()
    try:
        return repository.get_pending_reminders(db, limit=limit)
    finally:
        db.close()


def mark_as_reminded(nota_id: str):
    db = _db.SessionLocal()
    try:
        repository.mark_as_reminded(db, nota_id)
        log_event("scheduler_reminder_marked", reminder_id=nota_id)
    finally:
        db.close()


def notify_telegram(nota: dict) -> bool:
    """Envía un recordatorio a Telegram directamente via HTTP (sin depender del bot)."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        log_event(
            "scheduler_telegram_not_configured",
            level="WARNING",
            reminder_id=nota.get("id"),
        )
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    message = f"Recordatorio:\n{nota['content']}"

    for attempt in range(1, REMINDER_MAX_RETRIES + 1):
        try:
            resp = requests.post(
                url,
                json={"chat_id": TELEGRAM_CHAT_ID, "text": message},
                timeout=10,
            )
            resp.raise_for_status()
            log_event(
                "scheduler_reminder_sent",
                reminder_id=nota.get("id"),
                attempt=attempt,
            )
            return True
        except Exception as exc:
            log_event(
                "scheduler_reminder_send_failed",
                level="WARNING",
                reminder_id=nota.get("id"),
                attempt=attempt,
                error=str(exc),
            )
            if attempt < REMINDER_MAX_RETRIES:
                time.sleep(REMINDER_RETRY_DELAY_SECONDS)

    log_event(
        "scheduler_reminder_send_exhausted",
        level="ERROR",
        reminder_id=nota.get("id"),
        max_retries=REMINDER_MAX_RETRIES,
    )
    return False


def run_scheduler():
    print("Scheduler iniciado...")
    log_event("scheduler_started")

    while True:
        reminders = get_due_reminders()

        if reminders:
            print(f"\n{len(reminders)} recordatorio(s) pendiente(s):")
            for reminder in reminders:
                print("-", reminder["content"])
                sent = notify_telegram(reminder)
                if sent:
                    mark_as_reminded(reminder["id"])
                    bus.publish("recordatorio.enviado", {"id": reminder["id"]})
        else:
            print("Sin recordatorios pendientes")

        time.sleep(SCHEDULER_INTERVAL_SECONDS)
