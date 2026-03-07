import json
import os
import time
from datetime import datetime

from academiaserver.config import INBOX_DIR, SCHEDULER_INTERVAL_SECONDS
from academiaserver.logger import log_event


def load_notes():
    notes = []

    if not os.path.exists(INBOX_DIR):
        return notes

    for file in os.listdir(INBOX_DIR):
        if not file.endswith(".json"):
            continue

        path = os.path.join(INBOX_DIR, file)
        with open(path, "r", encoding="utf-8") as f:
            notes.append(json.load(f))

    return notes


def get_due_reminders():
    reminders = []

    for note in load_notes():
        if note.get("type") != "recordatorio":
            continue

        metadata = note.get("metadata", {})
        if metadata.get("reminded") is True:
            continue

        dt = metadata.get("datetime")
        if not dt:
            continue

        try:
            reminder_time = datetime.fromisoformat(dt)
        except ValueError:
            log_event(
                "scheduler_invalid_datetime",
                level="WARNING",
                reminder_id=note.get("id"),
                raw_datetime=dt,
            )
            continue

        if reminder_time <= datetime.now():
            reminders.append(note)

    if reminders:
        log_event("scheduler_due_reminders_found", count=len(reminders))

    return reminders


def get_pending_reminders(limit: int = 5):
    pending = []
    for note in load_notes():
        if note.get("type") != "recordatorio":
            continue

        metadata = note.get("metadata", {})
        if metadata.get("reminded") is True:
            continue

        dt = metadata.get("datetime")
        if not dt:
            continue

        try:
            reminder_time = datetime.fromisoformat(dt)
        except ValueError:
            continue

        pending.append((reminder_time, note))

    pending.sort(key=lambda x: x[0])
    return [note for _, note in pending[:limit]]


def mark_as_reminded(note):
    note.setdefault("metadata", {})
    note["metadata"]["reminded"] = True

    path = os.path.join(INBOX_DIR, f"{note['id']}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(note, f, indent=4, ensure_ascii=False)
    log_event("scheduler_reminder_marked", reminder_id=note.get("id"))


def run_scheduler():
    print("Scheduler iniciado...")
    log_event("scheduler_started")

    while True:
        reminders = get_due_reminders()

        if reminders:
            print("\nRecordatorios pendientes:")
            for reminder in reminders:
                print("-", reminder["content"])
                mark_as_reminded(reminder)
        else:
            print("Sin recordatorios pendientes")

        time.sleep(SCHEDULER_INTERVAL_SECONDS)
