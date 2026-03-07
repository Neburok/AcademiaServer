def build_contextual_reply(note: dict) -> str:
    note_type = note.get("type", "nota")
    title = note.get("title", "Sin titulo")
    metadata = note.get("metadata", {})
    enrichment = metadata.get("enrichment", {})
    topics = enrichment.get("topics", [])
    main_topic = topics[0] if topics else None

    if note_type == "recordatorio":
        dt = metadata.get("datetime")
        if dt:
            return f"Recordatorio guardado para {dt}. Titulo: {title}."
        return (
            "Recordatorio guardado sin fecha/hora confirmada. "
            "Indica fecha y hora en formato: 'mañana a las 18:30'."
        )

    if note_type == "idea":
        if main_topic:
            return f"Idea registrada: {title}. Tema detectado: {main_topic}."
        return f"Idea registrada: {title}."

    if note_type == "tarea":
        priority = metadata.get("ai", {}).get("priority", "media")
        return f"Tarea guardada: {title}. Prioridad sugerida: {priority}."

    if note_type == "pregunta":
        return (
            f"Pregunta registrada: {title}. "
            "Si quieres, puedo buscar notas relacionadas."
        )

    if main_topic:
        return f"Nota guardada: {title}. Tema detectado: {main_topic}."
    return f"Nota guardada: {title}."
