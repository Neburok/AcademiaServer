NOTE_SCHEMA_VERSION = "1.0.0"


def canonicalize_note(note: dict) -> dict:
    canonical = dict(note)
    canonical.setdefault("schema_version", NOTE_SCHEMA_VERSION)
    canonical.setdefault("type", "nota")
    canonical.setdefault("title", canonical.get("content", "")[:60])
    canonical.setdefault("tags", [])
    canonical.setdefault("metadata", {})
    canonical.setdefault("links", [])
    canonical.setdefault("source", "unknown")
    canonical["metadata"].setdefault("enrichment", {})
    return canonical
