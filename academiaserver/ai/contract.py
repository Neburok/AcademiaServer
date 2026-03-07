from datetime import datetime


ALLOWED_TYPES = {"nota", "recordatorio", "idea", "tarea", "pregunta"}
ALLOWED_PRIORITIES = {"baja", "media", "alta"}


def _as_text(value, default=""):
    if value is None:
        return default
    return str(value).strip()


def _normalize_tags(tags):
    if tags is None:
        return []
    if not isinstance(tags, list):
        raise ValueError("tags debe ser una lista")

    normalized = []
    for tag in tags:
        text = _as_text(tag).lower()
        if not text:
            continue
        if text not in normalized:
            normalized.append(text)
    return normalized[:5]


def _validate_datetime(value):
    if value in (None, "", "null"):
        return None
    text = _as_text(value)
    datetime.fromisoformat(text)
    return text


def validate_ai_analysis(analysis: dict) -> dict:
    if not isinstance(analysis, dict):
        raise ValueError("La salida de IA debe ser un objeto JSON")

    note_type = _as_text(analysis.get("note_type"), default="nota").lower()
    if note_type not in ALLOWED_TYPES:
        raise ValueError(f"note_type no permitido: {note_type}")

    title = _as_text(analysis.get("title"))
    if not title:
        raise ValueError("title es obligatorio")
    if len(title) > 60:
        title = title[:60].strip()

    summary = _as_text(analysis.get("summary"))
    if len(summary) > 280:
        summary = summary[:280].strip()

    priority = _as_text(analysis.get("priority"), default="media").lower()
    if priority not in ALLOWED_PRIORITIES:
        raise ValueError(f"priority no permitida: {priority}")

    reply_text = _as_text(analysis.get("reply_text"))
    if len(reply_text) > 220:
        raise ValueError("reply_text excede 220 caracteres")

    normalized = {
        "note_type": note_type,
        "title": title,
        "summary": summary,
        "tags": _normalize_tags(analysis.get("tags")),
        "priority": priority,
        "datetime": _validate_datetime(analysis.get("datetime")),
        "reply_text": reply_text,
    }
    return normalized
