"""Tests para AgentRouter — detección de intención y routing a agentes educativos."""
import unittest
from unittest.mock import MagicMock

from academiaserver.ai.agent_router import AgentRouter
from academiaserver.ai.agents.planning import PlanningAgent
from academiaserver.ai.agents.script import ScriptAgent
from academiaserver.ai.agents.slides import SlidesAgent


class TestDeteccionDeTiposDeTarea(unittest.TestCase):
    """Verifica que detect_task_type identifica correctamente cada tipo."""

    def setUp(self):
        self.router = AgentRouter(provider=MagicMock())

    # ── Planeación ────────────────────────────────────────────────────────────

    def test_detecta_planeacion_didactica_con_tilde(self):
        self.assertEqual(self.router.detect_task_type("planeación didáctica de Física I"), "planeacion")

    def test_detecta_planeacion_sin_tilde(self):
        self.assertEqual(self.router.detect_task_type("planeacion didactica de termodinámica"), "planeacion")

    def test_detecta_genera_planeacion(self):
        self.assertEqual(self.router.detect_task_type("genera una planeación para la Unidad 3"), "planeacion")

    def test_detecta_hazme_planeacion(self):
        self.assertEqual(self.router.detect_task_type("hazme una planeación de Cálculo diferencial"), "planeacion")

    def test_detecta_plan_de_clase(self):
        self.assertEqual(self.router.detect_task_type("necesito el plan de clase para mañana"), "planeacion")

    def test_detecta_planear_unidad(self):
        self.assertEqual(self.router.detect_task_type("quiero planear la unidad de cinemática"), "planeacion")

    # ── Guión ────────────────────────────────────────────────────────────────

    def test_detecta_guion_de_clase(self):
        self.assertEqual(self.router.detect_task_type("guión de clase de Termodinámica"), "guion")

    def test_detecta_guion_sin_tilde(self):
        self.assertEqual(self.router.detect_task_type("guion de clase de hoy"), "guion")

    def test_detecta_guion_tecnopedagogico(self):
        self.assertEqual(self.router.detect_task_type("hazme el guión tecnopedagógico"), "guion")

    def test_detecta_genera_guion(self):
        self.assertEqual(self.router.detect_task_type("genera el guión para la clase de mañana"), "guion")

    def test_detecta_secuencia_de_actividades(self):
        self.assertEqual(self.router.detect_task_type("secuencia de actividades para hoy"), "guion")

    # ── Slides ───────────────────────────────────────────────────────────────

    def test_detecta_diapositivas(self):
        self.assertEqual(self.router.detect_task_type("prepara las diapositivas de termodinámica"), "slides")

    def test_detecta_slides_en_ingles(self):
        self.assertEqual(self.router.detect_task_type("necesito slides para mi presentación"), "slides")

    def test_detecta_presentacion_de(self):
        self.assertEqual(self.router.detect_task_type("haz una presentación de la Ley de Ohm"), "slides")

    def test_detecta_genera_diapositivas(self):
        self.assertEqual(self.router.detect_task_type("genera las diapositivas para el parcial"), "slides")

    def test_detecta_hazme_diapos(self):
        self.assertEqual(self.router.detect_task_type("hazme las diapos de esta semana"), "slides")

    # ── No docente ───────────────────────────────────────────────────────────

    def test_no_detecta_nota_normal(self):
        self.assertIsNone(self.router.detect_task_type("hoy aprendí sobre transformadas de Laplace"))

    def test_no_detecta_recordatorio(self):
        self.assertIsNone(self.router.detect_task_type("recuérdame revisar el artículo mañana"))

    def test_no_detecta_idea_normal(self):
        self.assertIsNone(self.router.detect_task_type("idea: usar Python en los laboratorios"))

    def test_no_detecta_pregunta_general(self):
        self.assertIsNone(self.router.detect_task_type("¿qué apuntes tengo de cinemática?"))

    def test_no_detecta_mensaje_vacio(self):
        self.assertIsNone(self.router.detect_task_type(""))


class TestGetAgent(unittest.TestCase):
    """Verifica que get_agent devuelve la instancia correcta."""

    def setUp(self):
        self.router = AgentRouter(provider=MagicMock())

    def test_get_agent_planeacion(self):
        self.assertIsInstance(self.router.get_agent("planeacion"), PlanningAgent)

    def test_get_agent_guion(self):
        self.assertIsInstance(self.router.get_agent("guion"), ScriptAgent)

    def test_get_agent_slides(self):
        self.assertIsInstance(self.router.get_agent("slides"), SlidesAgent)

    def test_get_agent_desconocido_retorna_none(self):
        self.assertIsNone(self.router.get_agent("asistencia"))


class TestRoute(unittest.TestCase):
    """Verifica que route() devuelve None para notas normales y procesa tareas educativas."""

    def setUp(self):
        self.mock_provider = MagicMock()
        self.router = AgentRouter(provider=self.mock_provider)

    def test_route_retorna_none_para_nota_normal(self):
        resultado = self.router.route(
            "hoy dicté clase sobre deriva de las especies",
            context=[],
            memory=[],
        )
        self.assertIsNone(resultado)

    def test_route_llama_al_agente_correcto_para_planeacion(self):
        # Mockear el provider para que el agente pueda procesar
        self.mock_provider.analyze_message.return_value = {
            "note_type": "planeacion",
            "title": "Planeación Física I",
            "summary": "Resumen",
            "tags": [],
            "priority": "alta",
            "datetime": None,
            "reply_text": "¿Para qué unidad, Profesor?",
            "entities": [],
            "topics": ["docencia"],
            "missing_info": ["unidad"],
        }

        resultado = self.router.route(
            "genera una planeación para Física I",
            context=[],
            memory=[],
        )

        self.assertIsNotNone(resultado)
        note, reply_text = resultado
        self.assertEqual(note["type"], "planeacion")
        self.assertIn("Profesor", reply_text)


if __name__ == "__main__":
    unittest.main()
