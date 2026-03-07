import re
import unicodedata


SENSITIVE_PATTERNS = [
    "password",
    "contrasena",
    "api key",
    "token",
    "secreto",
    "credencial",
    "cuenta bancaria",
    "tarjeta",
    "curp",
    "rfc",
]


def normalize_text(text: str) -> str:
    lowered = text.lower().strip()
    normalized = unicodedata.normalize("NFD", lowered)
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    return " ".join(normalized.split())


def is_sensitive_message(text: str) -> bool:
    normalized = normalize_text(text)
    return any(pattern in normalized for pattern in SENSITIVE_PATTERNS)
