"""
Clase base para agentes educativos especializados de Mitzlia.

Cada subclase implementa un tipo de tarea docente (planeación, guión, diapositivas).
Los agentes usan el mismo provider de IA que el AIOrchestrator, pero inyectan
su propio system prompt especializado en lugar del prompt genérico de Mitzlia.
"""
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Instrucciones de esquema JSON comunes a todos los agentes educativos
_ESQUEMA_JSON = """
Reglas de respuesta:
1) Devuelve ÚNICAMENTE un JSON válido, sin texto fuera del objeto.
2) reply_text:
   · Si falta información → haz UNA sola pregunta (máx. 500 chars).
   · Si tienes TODOS los datos → genera el contenido completo en Markdown (sin límite).
3) missing_info: lista de campos que aún necesitas. Si tienes todo, usa [].
4) title: máximo 60 caracteres.
5) tags: lista de 0 a 5 elementos en minúsculas.
6) priority: solo "baja", "media" o "alta".

Esquema JSON de salida:
{
  "note_type": "<tipo de tarea>",
  "title": "Título descriptivo (máx. 60 caracteres)",
  "summary": "Resumen breve",
  "tags": ["tag1", "tag2"],
  "priority": "alta",
  "datetime": null,
  "reply_text": "Respuesta de Mitzlia al Profesor",
  "entities": ["entidad1"],
  "topics": ["docencia"],
  "missing_info": ["campo_faltante_1"]
}
""".strip()

_MAX_QUESTION_CHARS = 1000  # límite para preguntas durante el multi-turno
_TELEGRAM_MAX_CHARS = 4000  # margen sobre el límite de 4096 de Telegram


class EducationalAgent(ABC):
    """
    Agente educativo especializado para tareas docentes de Mitzlia.

    Cada subclase define:
    - TASK_TYPE: identificador del tipo de tarea ("planeacion", "guion", "slides")
    - _task_system_prompt(): instrucciones específicas para la IA

    El agente:
    1. Construye un system prompt combinando las instrucciones de la tarea y el esquema JSON
    2. Llama al provider de IA con ese prompt
    3. Extrae reply_text y missing_info del resultado
    4. Construye el dict de nota con type = TASK_TYPE
    """

    TASK_TYPE: str

    def __init__(self, provider):
        self.provider = provider

    @abstractmethod
    def _task_system_prompt(self) -> str:
        """Instrucciones específicas para este tipo de tarea docente."""

    def _build_system_prompt(self) -> str:
        return f"{self._task_system_prompt()}\n\n{_ESQUEMA_JSON}"

    def process(self, text: str, context: list, memory: list) -> tuple[dict, str]:
        """
        Procesa el mensaje con el provider usando el prompt especializado.

        Retorna (note_dict, reply_text).
        Degradación suave: si el provider falla, retorna una respuesta genérica
        pidiendo al Profesor que reformule.
        """
        try:
            raw = self.provider.analyze_message(
                text,
                context=context,
                memory=memory,
                system_prompt_override=self._build_system_prompt(),
            )
        except Exception as exc:
            logger.warning("EducationalAgent '%s' falló: %s", self.TASK_TYPE, exc)
            return self._fallback_note(text), self._default_reply()

        reply_text = str(raw.get("reply_text") or "").strip()
        if not reply_text:
            reply_text = self._default_reply()

        # Truncar solo si es una pregunta (missing_info no vacío); los documentos
        # completos (missing_info == []) se entregan sin recortar.
        missing_info_raw = raw.get("missing_info")
        missing_info = missing_info_raw if isinstance(missing_info_raw, list) else []
        if missing_info and len(reply_text) > _MAX_QUESTION_CHARS:
            reply_text = reply_text[:_MAX_QUESTION_CHARS]

        note = self._build_note(text, raw)
        return note, reply_text

    def _build_note(self, text: str, analysis: dict) -> dict:
        """Construye el dict de nota a partir del análisis de la IA."""
        tags = analysis.get("tags")
        topics = analysis.get("topics")
        entities = analysis.get("entities")
        missing_info = analysis.get("missing_info")

        return {
            "content": text,
            "type": self.TASK_TYPE,
            "title": (str(analysis.get("title") or text[:60]))[:60].strip(),
            "tags": tags if isinstance(tags, list) else [],
            "metadata": {
                "enrichment": {
                    "topics": topics if isinstance(topics, list) else ["docencia"],
                    "summary": str(analysis.get("summary") or ""),
                    "priority": analysis.get("priority", "alta"),
                    "entities": entities if isinstance(entities, list) else [],
                },
                "agent": self.TASK_TYPE,
                "missing_info": missing_info if isinstance(missing_info, list) else [],
            },
            "source": "telegram",
        }

    def _fallback_note(self, text: str) -> dict:
        """Nota mínima en caso de fallo del provider."""
        return {
            "content": text,
            "type": self.TASK_TYPE,
            "title": text[:60],
            "tags": [],
            "metadata": {
                "enrichment": {
                    "topics": ["docencia"],
                    "summary": "",
                    "priority": "alta",
                    "entities": [],
                },
                "agent": self.TASK_TYPE,
                "missing_info": [],
            },
            "source": "telegram",
        }

    def _default_reply(self) -> str:
        return "¿En qué puedo ayudarle con esa tarea, Profesor?"
