def extract_topics(text: str):
    lowered = text.lower()
    catalog = {
        "sem": ["sem", "microscopia", "caracterizacion"],
        "docencia": ["clase", "docencia", "curso", "estudiantes"],
        "investigacion": ["investigacion", "articulo", "experimento", "hipotesis"],
        "agenda": ["junta", "reunion", "cita", "recordatorio"],
    }

    topics = []
    for topic, keywords in catalog.items():
        if any(keyword in lowered for keyword in keywords):
            topics.append(topic)
    return topics


def infer_priority(text: str, note_type: str):
    lowered = text.lower()
    if note_type == "recordatorio":
        return "alta"
    if any(token in lowered for token in ["urgente", "hoy", "importante"]):
        return "alta"
    if any(token in lowered for token in ["despues", "pendiente", "idea"]):
        return "media"
    return "baja"


def enrich_note_metadata(note: dict) -> dict:
    metadata = note.setdefault("metadata", {})
    enrichment = metadata.setdefault("enrichment", {})
    content = note.get("content", "")
    note_type = note.get("type", "nota")

    # Solo rellenar con reglas los campos que la IA no haya poblado
    if not enrichment.get("topics"):
        enrichment["topics"] = extract_topics(content)
    if not enrichment.get("priority"):
        enrichment["priority"] = infer_priority(content, note_type)
    # entities y summary: solo se rellenan si vienen de IA; no hay fallback por reglas
    if "entities" not in enrichment:
        enrichment["entities"] = []
    if "summary" not in enrichment:
        enrichment["summary"] = " ".join(content.split()[:20])

    return note
