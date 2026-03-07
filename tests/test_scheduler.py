import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta

from academiaserver import config
from academiaserver.scheduler import reminders_scheduler


class SchedulerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="academiaserver_test_")
        self.original_config_inbox = config.INBOX_DIR
        self.original_scheduler_inbox = reminders_scheduler.INBOX_DIR
        config.INBOX_DIR = self.temp_dir
        reminders_scheduler.INBOX_DIR = self.temp_dir

    def tearDown(self):
        config.INBOX_DIR = self.original_config_inbox
        reminders_scheduler.INBOX_DIR = self.original_scheduler_inbox
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _save_note(self, note_id: str, payload: dict):
        path = os.path.join(self.temp_dir, f"{note_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def test_get_due_reminders_solo_devuelve_vencidos_no_enviados(self):
        now = datetime.now()

        due_note = {
            "id": "1",
            "type": "recordatorio",
            "content": "Recordatorio vencido",
            "metadata": {
                "datetime": (now - timedelta(minutes=5)).isoformat(),
                "reminded": False,
            },
        }
        future_note = {
            "id": "2",
            "type": "recordatorio",
            "content": "Recordatorio futuro",
            "metadata": {
                "datetime": (now + timedelta(minutes=30)).isoformat(),
                "reminded": False,
            },
        }
        sent_note = {
            "id": "3",
            "type": "recordatorio",
            "content": "Recordatorio enviado",
            "metadata": {
                "datetime": (now - timedelta(minutes=10)).isoformat(),
                "reminded": True,
            },
        }

        self._save_note("1", due_note)
        self._save_note("2", future_note)
        self._save_note("3", sent_note)

        due = reminders_scheduler.get_due_reminders()
        self.assertEqual(len(due), 1)
        self.assertEqual(due[0]["id"], "1")

    def test_mark_as_reminded_persiste_estado(self):
        note = {
            "id": "9",
            "type": "recordatorio",
            "content": "Enviar resumen",
            "metadata": {"datetime": datetime.now().isoformat(), "reminded": False},
        }
        self._save_note("9", note)

        reminders_scheduler.mark_as_reminded(note)

        path = os.path.join(self.temp_dir, "9.json")
        with open(path, "r", encoding="utf-8") as f:
            updated = json.load(f)

        self.assertTrue(updated["metadata"]["reminded"])


if __name__ == "__main__":
    unittest.main()
