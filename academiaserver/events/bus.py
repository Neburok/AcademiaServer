from collections import defaultdict
from typing import Callable

from academiaserver.logger import log_event


class EventBus:
    def __init__(self):
        self._handlers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event: str, handler: Callable):
        self._handlers[event].append(handler)

    def publish(self, event: str, payload: dict):
        for handler in self._handlers.get(event, []):
            try:
                handler(payload)
            except Exception as exc:
                log_event("bus_handler_error", level="ERROR", event=event, error=str(exc))


bus = EventBus()


def _log_nota_guardada(payload: dict):
    log_event("nota.guardada", nota_id=payload.get("id"), nota_type=payload.get("type"))


def _log_recordatorio_enviado(payload: dict):
    log_event("recordatorio.enviado", nota_id=payload.get("id"))


def _log_nota_enriquecida(payload: dict):
    log_event("nota.enriquecida", nota_id=payload.get("id"), topics=payload.get("topics", []))


bus.subscribe("nota.guardada", _log_nota_guardada)
bus.subscribe("recordatorio.enviado", _log_recordatorio_enviado)
bus.subscribe("nota.enriquecida", _log_nota_enriquecida)
