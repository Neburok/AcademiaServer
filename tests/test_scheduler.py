import unittest
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from academiaserver.db.database import Base
from academiaserver.db import models  # noqa: F401 — registra Nota en Base
from academiaserver.db import repository


def make_test_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


class SchedulerTests(unittest.TestCase):
    def setUp(self):
        self.db = make_test_session()

    def tearDown(self):
        self.db.close()

    def _save_reminder(self, nota_id: str, content: str, dt: datetime, reminded: bool):
        nota = {
            "id": nota_id,
            "content": content,
            "type": "recordatorio",
            "source": "test",
            "schema_version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "tags": [],
            "links": [],
            "metadata": {
                "datetime": dt.isoformat(),
                "reminded": reminded,
                "enrichment": {},
            },
        }
        repository.save_nota(self.db, nota)

    def test_get_due_reminders_solo_devuelve_vencidos_no_enviados(self):
        now = datetime.now()
        self._save_reminder("1", "Recordatorio vencido", now - timedelta(minutes=5), False)
        self._save_reminder("2", "Recordatorio futuro", now + timedelta(minutes=30), False)
        self._save_reminder("3", "Recordatorio enviado", now - timedelta(minutes=10), True)

        due = repository.get_due_reminders(self.db)
        self.assertEqual(len(due), 1)
        self.assertEqual(due[0]["id"], "1")

    def test_mark_as_reminded_persiste_estado(self):
        now = datetime.now()
        self._save_reminder("9", "Enviar resumen", now - timedelta(minutes=1), False)

        repository.mark_as_reminded(self.db, "9")

        updated = repository.get_nota_by_id(self.db, "9")
        self.assertIsNotNone(updated)
        self.assertTrue(updated["metadata"]["reminded"])

    def test_get_pending_reminders_retorna_no_enviados_ordenados(self):
        now = datetime.now()
        self._save_reminder("a", "Pronto", now + timedelta(hours=1), False)
        self._save_reminder("b", "Lejano", now + timedelta(hours=5), False)
        self._save_reminder("c", "Ya enviado", now - timedelta(hours=1), True)

        pending = repository.get_pending_reminders(self.db, limit=5)
        ids = [r["id"] for r in pending]
        self.assertIn("a", ids)
        self.assertIn("b", ids)
        self.assertNotIn("c", ids)


if __name__ == "__main__":
    unittest.main()
