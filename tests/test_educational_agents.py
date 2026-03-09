"""Tests para los agentes educativos: PlanningAgent, ScriptAgent, SlidesAgent."""
import unittest
from unittest.mock import MagicMock

from academiaserver.ai.agents.base import EducationalAgent
from academiaserver.ai.agents.planning import PlanningAgent
from academiaserver.ai.agents.script import ScriptAgent
from academiaserver.ai.agents.slides import SlidesAgent


def make_provider_mock(reply_text="Respuesta", missing_info=None, note_type=None):
    """Crea un mock de provider con respuesta configurable."""
    provider = MagicMock()
    provider.analyze_message.return_value = {
        "note_type": note_type or "planeacion",
        "title": "Título de prueba",
        "summary": "Resumen breve",
        "tags": ["docencia"],
        "priority": "alta",
        "datetime": None,
        "reply_text": reply_text,
        "entities": [],
        "topics": ["docencia"],
        "missing_info": missing_info if missing_info is not None else [],
    }
    return provider


class TestEducationalAgentBase(unittest.TestCase):
    """Tests del comportamiento base común a todos los agentes."""

    def test_planning_agent_tiene_task_type_correcto(self):
        agent = PlanningAgent(provider=MagicMock())
        self.assertEqual(agent.TASK_TYPE, "planeacion")

    def test_script_agent_tiene_task_type_correcto(self):
        agent = ScriptAgent(provider=MagicMock())
        self.assertEqual(agent.TASK_TYPE, "guion")

    def test_slides_agent_tiene_task_type_correcto(self):
        agent = SlidesAgent(provider=MagicMock())
        self.assertEqual(agent.TASK_TYPE, "slides")

    def test_task_type_en_nota_generada(self):
        """La nota construida por el agente lleva el TASK_TYPE correcto."""
        for AgentClass in (PlanningAgent, ScriptAgent, SlidesAgent):
            with self.subTest(agent=AgentClass.__name__):
                provider = make_provider_mock(note_type=AgentClass.TASK_TYPE)
                agent = AgentClass(provider=provider)
                note, _ = agent.process("texto de prueba", context=[], memory=[])
                self.assertEqual(note["type"], AgentClass.TASK_TYPE)


class TestPlanningAgentComportamiento(unittest.TestCase):
    """Tests específicos del PlanningAgent."""

    def test_pregunta_cuando_falta_informacion(self):
        """Si missing_info no está vacío, el agente devuelve una pregunta."""
        provider = make_provider_mock(
            reply_text="¿Para qué materia necesita la planeación, Profesor?",
            missing_info=["materia", "unidad"],
        )
        agent = PlanningAgent(provider=provider)
        note, reply_text = agent.process("quiero una planeación", context=[], memory=[])

        self.assertIn("Profesor", reply_text)
        self.assertEqual(note["metadata"]["missing_info"], ["materia", "unidad"])

    def test_genera_planeacion_cuando_tiene_todos_los_datos(self):
        """Con missing_info=[], el agente indica que la tarea está completa."""
        planeacion_md = (
            "# Planeación Didáctica — Física I, Unidad 2\n\n"
            "| Campo | Valor |\n|-------|-------|\n| Materia | Física I |"
        )
        provider = make_provider_mock(
            reply_text=planeacion_md,
            missing_info=[],
            note_type="planeacion",
        )
        agent = PlanningAgent(provider=provider)
        note, reply_text = agent.process(
            "Física I, Unidad 2, 8 sesiones, 2do cuatrimestre",
            context=[],
            memory=[],
        )

        self.assertEqual(note["metadata"]["missing_info"], [])
        self.assertIn("Planeación", reply_text)

    def test_nota_contiene_source_telegram(self):
        provider = make_provider_mock()
        agent = PlanningAgent(provider=provider)
        note, _ = agent.process("texto", context=[], memory=[])
        self.assertEqual(note["source"], "telegram")

    def test_nota_contiene_metadata_agent(self):
        provider = make_provider_mock(note_type="planeacion")
        agent = PlanningAgent(provider=provider)
        note, _ = agent.process("texto", context=[], memory=[])
        self.assertEqual(note["metadata"]["agent"], "planeacion")

    def test_default_reply_no_vacio(self):
        agent = PlanningAgent(provider=MagicMock())
        self.assertTrue(len(agent._default_reply()) > 0)


class TestScriptAgentComportamiento(unittest.TestCase):
    """Tests específicos del ScriptAgent."""

    def test_pregunta_por_tema_si_falta(self):
        provider = make_provider_mock(
            reply_text="¿Sobre qué tema es la clase, Profesor?",
            missing_info=["tema"],
            note_type="guion",
        )
        agent = ScriptAgent(provider=provider)
        note, reply_text = agent.process("hazme el guión", context=[], memory=[])

        self.assertIn("tema", reply_text.lower())
        self.assertNotEqual(note["metadata"]["missing_info"], [])

    def test_guion_completo_tiene_estructura(self):
        guion_md = (
            "## Apertura (~5 min)\n\n"
            "## Desarrollo (~35 min)\n\n"
            "## Cierre (~10 min)"
        )
        provider = make_provider_mock(
            reply_text=guion_md,
            missing_info=[],
            note_type="guion",
        )
        agent = ScriptAgent(provider=provider)
        note, reply_text = agent.process(
            "guión de clase de Termodinámica, 50 min, 3er cuatrimestre",
            context=[],
            memory=[],
        )

        self.assertEqual(note["metadata"]["missing_info"], [])
        self.assertIn("Apertura", reply_text)
        self.assertIn("Desarrollo", reply_text)
        self.assertIn("Cierre", reply_text)


class TestSlidesAgentComportamiento(unittest.TestCase):
    """Tests específicos del SlidesAgent."""

    def test_pregunta_por_tema_si_falta(self):
        provider = make_provider_mock(
            reply_text="¿Sobre qué tema es la presentación, Profesor?",
            missing_info=["tema"],
            note_type="slides",
        )
        agent = SlidesAgent(provider=provider)
        _, reply_text = agent.process("hazme diapositivas", context=[], memory=[])

        self.assertIn("tema", reply_text.lower())

    def test_outline_completo_tiene_portada(self):
        outline_md = (
            "# Outline de Presentación — Ley de Ohm\n\n"
            "## Slide 1 — Portada\n"
            "## Slide 2 — Agenda\n"
            "## Slide 3 — Ley de Ohm\n"
        )
        provider = make_provider_mock(
            reply_text=outline_md,
            missing_info=[],
            note_type="slides",
        )
        agent = SlidesAgent(provider=provider)
        note, reply_text = agent.process(
            "diapositivas de Ley de Ohm para estudiantes de 1er cuatrimestre",
            context=[],
            memory=[],
        )

        self.assertEqual(note["metadata"]["missing_info"], [])
        self.assertIn("Portada", reply_text)


class TestDegradacionSuave(unittest.TestCase):
    """Verifica que los agentes no fallan si el provider lanza excepción."""

    def test_fallback_si_provider_falla(self):
        provider = MagicMock()
        provider.analyze_message.side_effect = ConnectionError("Ollama no disponible")

        for AgentClass in (PlanningAgent, ScriptAgent, SlidesAgent):
            with self.subTest(agent=AgentClass.__name__):
                agent = AgentClass(provider=provider)
                note, reply_text = agent.process("texto", context=[], memory=[])

                # Debe retornar nota mínima sin lanzar excepción
                self.assertEqual(note["type"], AgentClass.TASK_TYPE)
                self.assertTrue(len(reply_text) > 0)

    def test_pregunta_no_supera_1000_chars(self):
        """Con missing_info != [], la pregunta se trunca a 1000 chars."""
        texto_largo = "x" * 5000
        provider = make_provider_mock(reply_text=texto_largo, missing_info=["materia"])
        agent = PlanningAgent(provider=provider)
        _, reply_text = agent.process("texto", context=[], memory=[])

        self.assertLessEqual(len(reply_text), 1000)

    def test_documento_completo_no_se_trunca(self):
        """Con missing_info=[], el documento llega completo sin truncar."""
        texto_largo = "# Documento completo\n" + ("Contenido " * 600)  # ~6000 chars
        provider = make_provider_mock(reply_text=texto_largo, missing_info=[])
        agent = PlanningAgent(provider=provider)
        _, reply_text = agent.process("texto", context=[], memory=[])

        # El documento completo NO debe ser truncado a 3000
        self.assertGreater(len(reply_text), 3000)


class TestSystemPromptOverride(unittest.TestCase):
    """Verifica que el agente inyecta su propio system prompt en el provider."""

    def test_provider_recibe_system_prompt_override(self):
        provider = make_provider_mock()
        agent = PlanningAgent(provider=provider)
        agent.process("quiero una planeación", context=[], memory=[])

        llamada = provider.analyze_message.call_args
        self.assertIn("system_prompt_override", llamada.kwargs)
        override = llamada.kwargs["system_prompt_override"]
        self.assertIsNotNone(override)
        self.assertIn("planeacion", override.lower())

    def test_system_prompt_contiene_esquema_json(self):
        provider = make_provider_mock()
        for AgentClass in (PlanningAgent, ScriptAgent, SlidesAgent):
            with self.subTest(agent=AgentClass.__name__):
                agent = AgentClass(provider=provider)
                agent.process("texto", context=[], memory=[])

                override = provider.analyze_message.call_args.kwargs.get(
                    "system_prompt_override", ""
                )
                self.assertIn("missing_info", override)
                self.assertIn("reply_text", override)


if __name__ == "__main__":
    unittest.main()
