from datetime import datetime


def _parse_iso(value: str):
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def generate_daily_digest(notes: list[dict], date_ref: datetime | None = None) -> dict:
    now = date_ref or datetime.now()
    today = now.date()

    today_notes = []
    today_reminders = []

    for note in notes:
        created = _parse_iso(note.get("created_at", ""))
        if created is None or created.date() != today:
            continue
        today_notes.append(note)
        if note.get("type") == "recordatorio":
            today_reminders.append(note)

    top_topics = {}
    for note in today_notes:
        topics = note.get("metadata", {}).get("enrichment", {}).get("topics", [])
        for topic in topics:
            top_topics[topic] = top_topics.get(topic, 0) + 1

    ordered_topics = sorted(top_topics.items(), key=lambda x: x[1], reverse=True)
    summary_topics = [topic for topic, _count in ordered_topics[:5]]

    lines = [
        f"Digest del dia {today.isoformat()}",
        f"Notas registradas: {len(today_notes)}",
        f"Recordatorios registrados: {len(today_reminders)}",
    ]
    if summary_topics:
        lines.append("Temas principales: " + ", ".join(summary_topics))
    else:
        lines.append("Temas principales: sin clasificar")

    return {
        "date": today.isoformat(),
        "notes_count": len(today_notes),
        "reminders_count": len(today_reminders),
        "top_topics": summary_topics,
        "text": "\n".join(lines),
    }
