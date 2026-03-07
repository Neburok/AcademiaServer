from academiaserver.processing.classifier import classify_note
from academiaserver.processing.enrichment import enrich_note_metadata
from academiaserver.processing.reminders import parse_reminder
from academiaserver.logger import log_event
from academiaserver.schemas import canonicalize_note


def process_note(text: str, source="unknown"):

    note_type = classify_note(text)
    log_event("pipeline_note_classified", source=source, note_type=note_type)

    note = {
        "content": text,
        "type": note_type,
        "title": generate_title(text),
        "tags": [],
        "metadata": {},
        "source": source
    }

    reminder_data = None
    if note_type == "recordatorio":
        reminder_data = parse_reminder(text)

    if reminder_data:
        note["metadata"].update(reminder_data)
        note["metadata"]["reminded"] = False
        log_event(
            "pipeline_reminder_detected",
            source=source,
            datetime=reminder_data.get("datetime"),
        )
    else:
        log_event("pipeline_note_processed", source=source, note_type=note_type)

    note = canonicalize_note(note)
    note = enrich_note_metadata(note)
    log_event(
        "pipeline_note_enriched",
        source=source,
        note_type=note_type,
        topics=note.get("metadata", {}).get("enrichment", {}).get("topics", []),
    )
    return note


def generate_title(text: str):

    words = text.split()

    return " ".join(words[:8])
