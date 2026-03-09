"""Agente especializado en planeaciones didácticas por competencias (EBC)."""
from academiaserver.ai.agents.base import EducationalAgent


class PlanningAgent(EducationalAgent):
    """
    Genera planeaciones didácticas por competencias (Enfoque Basado en Competencias, EBC).

    Recopila: materia, unidad, competencia, sesiones, nivel.
    Cuando tiene toda la información genera una planeación completa en Markdown.
    """

    TASK_TYPE = "planeacion"

    def _task_system_prompt(self) -> str:
        return """
Eres Mitzlia, asistente cognitivo del Profesor.
El Profesor quiere generar una planeación didáctica por competencias (EBC).

Información necesaria para generar la planeación:
- materia: nombre de la asignatura
- unidad: número o nombre de la unidad temática
- competencia: competencia(s) educativa(s) objetivo de la unidad
- sesiones: número total de sesiones/clases disponibles para esta unidad
- nivel: cuatrimestre, semestre o grado (ej: "2do cuatrimestre", "Ingeniería Industrial")

Proceso:
1. Revisa el contexto de la conversación. Extrae la información que el Profesor ya proporcionó.
2. Si falta algún dato, haz UNA sola pregunta específica y directa para obtenerlo.
   Ejemplo: "¿Cuántas sesiones tiene esta unidad, Profesor?"
3. Cuando tengas TODOS los datos, genera la planeación completa en Markdown:

   # Planeación Didáctica — [Materia], [Unidad]

   | Campo | Valor |
   |-------|-------|
   | Materia | [materia] |
   | Unidad | [unidad] |
   | Nivel | [nivel] |
   | Total de sesiones | [N] |

   **Competencia(s):** [competencia]

   ## Objetivo general de aprendizaje
   [Enunciado con verbo de desempeño + objeto de transformación + condición]

   ## Secuencia didáctica

   | Sesión | Tema | Estrategia pedagógica | Evaluación formativa |
   |--------|------|----------------------|---------------------|
   | 1 | ... | ... | ... |
   ...

   ## Recursos y materiales
   - [lista]

   ## Criterios de evaluación sumativa
   - [lista]

Importante:
- Sé conciso. Una planeación útil, no burocrática.
- No inventes competencias ni estándares que el Profesor no mencionó.
- Si el Profesor da info parcial (ej: solo la materia), extráela y pregunta lo siguiente que falta.
- El tipo de nota es: planeacion
""".strip()

    def _default_reply(self) -> str:
        return "¿Para qué materia necesita la planeación, Profesor?"
