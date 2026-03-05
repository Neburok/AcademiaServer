from academiaserver.processing.classifier import classify_note
from academiaserver.processing.reminders import parse_reminder


def process_note(text: str, source="unknown"):

    note_type = classify_note(text)

    note = {
        "content": text,
        "type": note_type,
        "title": generate_title(text),
        "tags": [],
        "metadata": {},
        "source": source
    }

    if note_type == "recordatorio":
        reminder_data = parse_reminder(text)

        if reminder_data:
            note["metadata"].update(reminder_data)

    return note

def generate_title(text: str):

    words = text.split()

    return " ".join(words[:8])