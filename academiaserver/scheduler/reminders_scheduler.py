import os
import json
import time
from datetime import datetime

INBOX_DIR = "inbox"


def load_notes():

    notes = []

    if not os.path.exists(INBOX_DIR):
        return notes

    for file in os.listdir(INBOX_DIR):
        if file.endswith(".json"):
            path = os.path.join(INBOX_DIR, file)
            with open(path, "r", encoding="utf-8") as f:
                note = json.load(f)
                notes.append(note)

    return notes


def get_due_reminders():
    now = datetime.now()
    reminders = []

    for note in load_notes():
        if note.get("type") != "recordatorio":
            continue
        dt = note.get("metadata", {}).get("datetime")
        if not dt:
            continue

        reminder_time = datetime.fromisoformat(dt)

        if reminder_time <= now:
            reminders.append(note)

    return reminders


def run_scheduler():

    print("Scheduler iniciado...")

    while True:
        reminders = get_due_reminders()
        if reminders:
            print("Recordatorios pendientes:")
            for r in reminders:
                print(r["content"])

        time.sleep(60)