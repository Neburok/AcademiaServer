import unittest
from unittest.mock import patch

from academiaserver.processing.pipeline import process_note


class PipelineTests(unittest.TestCase):
    def test_procesa_nota_normal_sin_error(self):
        note = process_note("Idea para clase de transferencia de calor", source="test")
        self.assertEqual(note["type"], "nota")
        self.assertIn("enrichment", note["metadata"])
        self.assertIn("priority", note["metadata"]["enrichment"])
        self.assertIn("schema_version", note)
        self.assertEqual(note["source"], "test")

    @patch(
        "academiaserver.processing.pipeline.parse_reminder",
        return_value={"datetime": "2026-03-10T08:00:00"},
    )
    def test_procesa_recordatorio_y_marca_reminded_false(self, _mock_reminder):
        note = process_note("Recuerdame revisar el articulo", source="test")
        self.assertEqual(note["type"], "recordatorio")
        self.assertEqual(note["metadata"]["datetime"], "2026-03-10T08:00:00")
        self.assertFalse(note["metadata"]["reminded"])
        self.assertIn("enrichment", note["metadata"])


if __name__ == "__main__":
    unittest.main()
