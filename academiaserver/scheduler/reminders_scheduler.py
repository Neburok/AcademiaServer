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

    reminders = []

    for note in load_notes():

        if note.get("type") != "recordatorio":
            continue

        metadata = note.get("metadata", {})

        # 👇 ignorar recordatorios ya enviados
        if metadata.get("reminded") is True:
            continue

        dt = metadata.get("datetime")

        if not dt:
            continue

        reminder_time = datetime.fromisoformat(dt)

        if reminder_time <= datetime.now():
            reminders.append(note)

    return reminders


def mark_as_reminded(note):

    note["metadata"]["reminded"] = True

    path = os.path.join(INBOX_DIR, f"{note['id']}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(note, f, indent=4, ensure_ascii=False)


def run_scheduler():

    print("Scheduler iniciado...")

    while True:

        reminders = get_due_reminders()

        if reminders:

            print("\nRecordatorios pendientes:")

            for r in reminders:

                print("-", r["content"])

                # 👇 marcar recordatorio como procesado
                mark_as_reminded(r)

        else:
            print("Sin recordatorios pendientes")

        time.sleep(60)