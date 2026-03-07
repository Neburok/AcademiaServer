import unittest
from unittest.mock import patch

from academiaserver.ai.orchestrator import AIOrchestrator


class FakeProviderOk:
    def analyze_message(self, _text: str) -> dict:
        return {
            "note_type": "idea",
            "title": "Idea para mejorar clase de SEM",
            "summary": "Propuesta de mejora docente.",
            "tags": ["sem", "docencia"],
            "priority": "media",
            "datetime": None,
            "reply_text": "Idea registrada. Podemos convertirla en proyecto.",
        }


class FakeProviderFail:
    def analyze_message(self, _text: str) -> dict:
        raise RuntimeError("Fallo simulado de IA")


class FakeProviderReminderNoDatetime:
    def analyze_message(self, _text: str) -> dict:
        return {
            "note_type": "recordatorio",
            "title": "Revisar articulo",
            "summary": "Recordatorio sin fecha.",
            "tags": ["articulo"],
            "priority": "alta",
            "datetime": None,
            "reply_text": "Recordatorio registrado.",
        }


class FakeProviderIdeaNoReply:
    def analyze_message(self, _text: str) -> dict:
        return {
            "note_type": "idea",
            "title": "Idea de proyecto SEM",
            "summary": "Vincular notas de SEM",
            "tags": ["sem"],
            "priority": "media",
            "datetime": None,
            "reply_text": "   ",
        }


class FakeProviderInvalid:
    def analyze_message(self, _text: str) -> dict:
        return {
            "note_type": "otro_tipo",
            "title": "",
            "summary": "x",
            "tags": "no_lista",
            "priority": "superalta",
            "datetime": "fecha_mala",
            "reply_text": "",
        }


class FakeProviderPastDatetime:
    def analyze_message(self, _text: str) -> dict:
        return {
            "note_type": "recordatorio",
            "title": "Revisar articulo",
            "summary": "Recordatorio con fecha pasada",
            "tags": ["articulo"],
            "priority": "media",
            "datetime": "2024-03-08T19:42:00",
            "reply_text": "Recordatorio guardado.",
        }


class AIOrchestratorTests(unittest.TestCase):
    def test_ai_orchestrator_construye_nota_desde_ia(self):
        orchestrator = AIOrchestrator(provider=FakeProviderOk(), ai_max_retries=1)
        note, reply = orchestrator.process_message(
            "Tengo una idea para mejorar la clase de SEM", source="test"
        )

        self.assertEqual(note["type"], "idea")
        self.assertEqual(note["title"], "Idea para mejorar clase de SEM")
        self.assertEqual(note["source"], "test")
        self.assertEqual(note["schema_version"], "1.0.0")
        self.assertIn("enrichment", note["metadata"])
        self.assertIn("Idea registrada", reply)

    def test_ai_orchestrator_hace_fallback_a_reglas(self):
        orchestrator = AIOrchestrator(provider=FakeProviderFail(), ai_max_retries=1)
        note, reply = orchestrator.process_message(
            "Recuérdame revisar el artículo mañana a las 8", source="test"
        )

        self.assertIn(note["type"], {"recordatorio", "nota"})
        self.assertEqual(note["source"], "test")
        self.assertTrue(isinstance(reply, str) and len(reply) > 0)

    def test_ai_orchestrator_fallback_por_payload_invalido(self):
        orchestrator = AIOrchestrator(provider=FakeProviderInvalid(), ai_max_retries=1)
        note, reply = orchestrator.process_message(
            "Tengo una idea para experimento nuevo", source="test"
        )

        self.assertIn(note["type"], {"nota", "idea"})
        self.assertEqual(note["source"], "test")
        self.assertTrue(isinstance(reply, str) and len(reply) > 0)

    def test_recordatorio_sin_datetime_pide_aclaracion(self):
        orchestrator = AIOrchestrator(
            provider=FakeProviderReminderNoDatetime(), ai_max_retries=1
        )
        note, reply = orchestrator.process_message(
            "Recuérdame revisar el articulo", source="test"
        )

        self.assertEqual(note["type"], "recordatorio")
        self.assertTrue(note["metadata"].get("needs_clarification"))
        self.assertIn("Indica fecha y hora", reply)

    def test_respuesta_contextual_cuando_ia_no_da_reply(self):
        orchestrator = AIOrchestrator(provider=FakeProviderIdeaNoReply(), ai_max_retries=1)
        note, reply = orchestrator.process_message("Idea para organizar SEM", source="test")

        self.assertEqual(note["type"], "idea")
        self.assertIn("Idea registrada", reply)

    @patch(
        "academiaserver.ai.orchestrator.parse_reminder",
        return_value={"datetime": "2026-03-07T18:30:00"},
    )
    def test_recordatorio_ignora_datetime_pasado_de_ia(self, _mock_parser):
        orchestrator = AIOrchestrator(provider=FakeProviderPastDatetime(), ai_max_retries=1)
        note, _reply = orchestrator.process_message(
            "Recuérdame mañana a las 18:30 revisar el articulo", source="test"
        )

        self.assertEqual(note["type"], "recordatorio")
        self.assertEqual(note["metadata"]["datetime"], "2026-03-07T18:30:00")
        self.assertFalse(note["metadata"]["needs_clarification"])


if __name__ == "__main__":
    unittest.main()
