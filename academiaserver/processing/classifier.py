def classify_note(text: str):

    text = text.lower()

    triggers = [
        "recuérdame",
        "recuerdame",
        "recordar",
        "no olvidar"
    ]

    if any(t in text for t in triggers):
        return "recordatorio"

    return "nota"