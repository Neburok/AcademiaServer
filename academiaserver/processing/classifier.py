import unicodedata


def normalize_text(text: str) -> str:
    lowered = text.lower()
    decomposed = unicodedata.normalize("NFD", lowered)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def classify_note(text: str):
    normalized = normalize_text(text)

    triggers = [
        "recuerdame",
        "recordar",
        "no olvidar",
        "avisame",
        "avisa",
    ]

    if any(trigger in normalized for trigger in triggers):
        return "recordatorio"

    return "nota"
