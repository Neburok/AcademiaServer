"""
AgentRouter — detecta tareas docentes y enruta al agente educativo correspondiente.

Uso típico en telegram_bot.py:
    task_type = agent_router.detect_task_type(text)
    if task_type:
        agent = agent_router.get_agent(task_type)
        note, reply_text = agent.process(text, context=ctx, memory=memory)
"""
import re

from academiaserver.ai.agents.planning import PlanningAgent
from academiaserver.ai.agents.script import ScriptAgent
from academiaserver.ai.agents.slides import SlidesAgent

# ---------------------------------------------------------------------------
# Patrones de detección por tipo de tarea (regex en español)
# Se aplican sobre texto en minúsculas; las tildes se normalizan parcialmente
# usando clases de caracteres: [oó], [aá], etc.
# ---------------------------------------------------------------------------
_PATTERNS: dict[str, list[str]] = {
    "planeacion": [
        r"planeaci[oó]n\s+did[aá]ctica",
        r"planea(?:r|ci[oó]n)?\s+(?:la\s+)?(?:unidad|clase|materia|curso|asignatura)",
        r"plan\s+de\s+(?:clase|unidad|materia|curso|asignatura)",
        r"genera(?:r)?\s+(?:una?\s+)?planeaci",
        r"hazme\s+(?:una?\s+)?planeaci",
        r"necesito\s+(?:una?\s+)?planeaci[oó]n",
    ],
    "guion": [
        r"gui[oó]n\s+(?:de\s+(?:la\s+)?clase|tecnopedagóg|tecnopedagog)",
        r"guion\s+de\s+clase",
        r"secuencia\s+de\s+actividades",
        r"hazme\s+(?:el\s+)?gui[oó]n",
        r"genera(?:r)?\s+(?:el\s+)?gui[oó]n",
        r"script\s+de\s+clase",
        r"c[oó]mo\s+dar\s+la\s+clase",
    ],
    "slides": [
        r"\bdiapositivas?\b",
        r"presentaci[oó]n\s+(?:de|para|sobre)\b",
        r"\bslides?\b",
        r"prepara(?:r)?\s+(?:las?\s+)?diapo",
        r"hazme\s+(?:las?\s+)?diapo",
        r"genera(?:r)?\s+(?:las?\s+)?diapositivas?",
        r"\bpresentaci[oó]n\s+acad[eé]mica\b",
        r"\boutline\s+(?:de\s+)?(?:la\s+)?presentaci[oó]n\b",
    ],
}

# Compilar todos los patrones al cargar el módulo (eficiencia en el bot)
_COMPILED: dict[str, list[re.Pattern]] = {
    task_type: [re.compile(p, re.IGNORECASE) for p in patterns]
    for task_type, patterns in _PATTERNS.items()
}


class AgentRouter:
    """
    Detecta si un mensaje corresponde a una tarea docente y lo enruta al agente correcto.

    Los agentes comparten el mismo provider de IA que el AIOrchestrator; solo cambia
    el system prompt (inyectado vía system_prompt_override).
    """

    def __init__(self, provider):
        self._provider = provider
        self._agents: dict[str, "EducationalAgent"] = {
            "planeacion": PlanningAgent(provider),
            "guion": ScriptAgent(provider),
            "slides": SlidesAgent(provider),
        }

    def detect_task_type(self, text: str) -> str | None:
        """
        Intenta detectar el tipo de tarea docente en el texto.

        Retorna el task_type ("planeacion", "guion", "slides") o None si no hay match.
        """
        for task_type, patterns in _COMPILED.items():
            for pattern in patterns:
                if pattern.search(text):
                    return task_type
        return None

    def get_agent(self, task_type: str):
        """Devuelve el agente educativo para el tipo dado, o None si no existe."""
        return self._agents.get(task_type)

    def route(
        self,
        text: str,
        context: list,
        memory: list,
    ) -> tuple[dict, str] | None:
        """
        Detecta el tipo de tarea y enruta al agente correspondiente.

        Retorna (note_dict, reply_text) si fue enrutado, None si el mensaje
        no corresponde a ninguna tarea docente conocida.
        """
        task_type = self.detect_task_type(text)
        if task_type is None:
            return None
        agent = self._agents[task_type]
        return agent.process(text, context=context, memory=memory)
