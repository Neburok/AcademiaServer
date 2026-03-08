from datetime import datetime, timedelta

_MAX_FUTURE_DAYS = 365  # fechas más allá de 1 año se tratan como error de parseo

from academiaserver.ai.contract import validate_ai_analysis
from academiaserver.ai.replies import build_contextual_reply
from academiaserver.logger import log_event
from academiaserver.processing.enrichment import enrich_note_metadata
from academiaserver.processing.pipeline import process_note
from academiaserver.processing.reminders import parse_reminder
from academiaserver.schemas import canonicalize_note


class AIOrchestrator:
    def __init__(self, provider=None, ai_max_retries: int = 2):
        self.provider = provider
        self.ai_max_retries = max(1, ai_max_retries)

    def process_message(
        self,
        text: str,
        source: str = "telegram",
        context: list[str] = [],
        memory: list[dict] = [],
    ):
        if not self.provider:
            return self._fallback_rules(text, source, reason="ai_disabled")

        last_error = None
        for attempt in range(1, self.ai_max_retries + 1):
            try:
                raw_analysis = self.provider.analyze_message(text, context=context, memory=memory)
                analysis = validate_ai_analysis(raw_analysis)
                note = self._build_note_from_ai(text=text, source=source, analysis=analysis)
                reply_text = self._build_reply(note=note, ai_reply=analysis.get("reply_text"))
                log_event(
                    "ai_inference_ok",
                    source=source,
                    note_type=note.get("type"),
                    attempt=attempt,
                )
                return note, reply_text
            except Exception as exc:
                last_error = exc
                log_event(
                    "ai_inference_error",
                    level="WARNING",
                    source=source,
                    attempt=attempt,
                    error=str(exc),
                )

        return self._fallback_rules(text, source, reason=str(last_error))

    def _build_note_from_ai(self, text: str, source: str, analysis: dict) -> dict:
        note_type = analysis.get("note_type", "nota")

        note = {
            "content": text,
            "type": note_type,
            "title": (analysis.get("title") or text[:60]).strip(),
            "tags": analysis.get("tags") or [],
            "metadata": {
                "enrichment": {
                    "topics":   analysis.get("topics", []),
                    "entities": analysis.get("entities", []),
                    "summary":  analysis.get("summary", ""),
                    "priority": analysis.get("priority", "media"),
                },
                "ai": {
                    "provider": self.provider.__class__.__name__,
                },
            },
            "source": source,
        }

        dt = analysis.get("datetime")
        if note_type == "recordatorio":
            if dt:
                try:
                    parsed_dt = datetime.fromisoformat(dt)
                    now = datetime.now()
                    if parsed_dt < now:
                        dt = None
                        log_event(
                            "ai_datetime_past_ignored",
                            level="WARNING",
                            source=source,
                            ai_datetime=analysis.get("datetime"),
                        )
                    elif parsed_dt > now + timedelta(days=_MAX_FUTURE_DAYS):
                        dt = None
                        log_event(
                            "ai_datetime_far_future_ignored",
                            level="WARNING",
                            source=source,
                            ai_datetime=analysis.get("datetime"),
                            max_days=_MAX_FUTURE_DAYS,
                        )
                except ValueError:
                    dt = None

            if dt:
                note["metadata"]["datetime"] = dt
                note["metadata"]["reminded"] = False
                note["metadata"]["needs_clarification"] = False
            else:
                parsed = parse_reminder(text)
                if parsed:
                    note["metadata"].update(parsed)
                    note["metadata"]["reminded"] = False
                    note["metadata"]["needs_clarification"] = False
                else:
                    note["metadata"]["needs_clarification"] = True
                    note["metadata"]["clarification_prompt"] = (
                        "¿Cuándo, Profesor? Dígame fecha y hora, "
                        "por ejemplo: 'mañana a las 18:30'."
                    )

        note = canonicalize_note(note)
        note = enrich_note_metadata(note)
        return note

    def _fallback_rules(self, text: str, source: str, reason: str):
        note = process_note(text, source=source)
        log_event(
            "ai_fallback_rules",
            level="INFO",
            source=source,
            note_type=note.get("type"),
            reason=reason,
        )
        return note, self._build_reply(note=note, ai_reply=None)

    def _build_reply(self, note: dict, ai_reply: str | None) -> str:
        metadata = note.get("metadata", {})
        if metadata.get("needs_clarification") is True:
            return metadata.get("clarification_prompt") or (
                "¿Cuándo, Profesor? Necesito fecha y hora para el recordatorio."
            )

        if ai_reply:
            ai_reply = ai_reply.strip()
            if ai_reply:
                return ai_reply

        return build_contextual_reply(note)
