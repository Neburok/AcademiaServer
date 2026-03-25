"""Proveedor Claude — interfaz directa a Anthropic API."""
import json

import anthropic

from academiaserver.config import (
    ANTHROPIC_API_KEY,
    ANTHROPIC_CHAT_MODEL,
    ANTHROPIC_MAX_TOKENS,
)
from academiaserver.logger import log_event

_SYSTEM_PROMPT = """
Eres Mitzlia, asistente cognitiva académica del Profesor.
Analizas cada mensaje y respondes ÚNICAMENTE con un JSON válido. Sin texto fuera del JSON.

Esquema de respuesta:
{
  "type": "nota" | "recordatorio" | "pregunta",
  "title": "Título breve (máx. 60 caracteres)",
  "summary": "Resumen de una línea",
  "tags": ["tag1", "tag2"],
  "priority": "baja" | "media" | "alta",
  "reminder_datetime": "YYYY-MM-DDTHH:MM:SS si es recordatorio, null si no",
  "reply_text": "Respuesta breve y directa al Profesor (máx. 2 oraciones)"
}

Reglas de clasificación:
- "recordatorio": el mensaje pide recordar algo en una fecha/hora futura.
- "pregunta": el mensaje pregunta por notas, ideas o información ya registrada.
- "nota": cualquier otra cosa (idea, reflexión, concepto, tarea).

Reglas de respuesta:
- reply_text: tono directo, sin floreos. Confirma lo que guardaste o responde la pregunta.
- Si es recordatorio sin fecha clara, pon reminder_datetime: null y pregunta la fecha en reply_text.
""".strip()


class ClaudeProvider:
    def __init__(self):
        self._client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def analyze(self, text: str, context: list[dict] = []) -> dict:
        """
        Analiza un mensaje y retorna un dict con type, title, summary, tags,
        priority, reminder_datetime y reply_text.
        """
        messages = []

        # Incluir contexto conversacional (últimos 4 turnos)
        for turn in context[-4:]:
            if turn.get("user"):
                messages.append({"role": "user", "content": turn["user"]})
            if turn.get("assistant"):
                messages.append({"role": "assistant", "content": turn["assistant"]})

        messages.append({"role": "user", "content": text})

        try:
            response = self._client.messages.create(
                model=ANTHROPIC_CHAT_MODEL,
                max_tokens=ANTHROPIC_MAX_TOKENS,
                system=_SYSTEM_PROMPT,
                messages=messages,
            )
            raw = response.content[0].text.strip()

            # Limpiar bloque markdown si Claude lo envuelve en ```json
            if raw.startswith("```"):
                raw = raw.strip("`").lstrip("json").strip()

            result = json.loads(raw)
            log_event("claude_analyze_ok", note_type=result.get("type"))
            return result

        except json.JSONDecodeError as exc:
            log_event("claude_json_parse_error", level="WARNING", error=str(exc))
            return _fallback(text)
        except Exception as exc:
            log_event("claude_api_error", level="WARNING", error=str(exc))
            return _fallback(text)


def _fallback(text: str) -> dict:
    """Respuesta mínima cuando Claude no está disponible."""
    from academiaserver.processing.classifier import classify_note
    from academiaserver.processing.reminders import parse_reminder

    note_type = classify_note(text)
    result = {
        "type": note_type,
        "title": text[:60].strip(),
        "summary": "",
        "tags": [],
        "priority": "media",
        "reminder_datetime": None,
        "reply_text": "Guardado, Profesor." if note_type == "nota" else "Anotado.",
    }
    if note_type == "recordatorio":
        parsed = parse_reminder(text)
        if parsed:
            result["reminder_datetime"] = parsed.get("datetime")
    return result
