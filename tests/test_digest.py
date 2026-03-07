import unittest
from datetime import datetime

from academiaserver.digest import generate_daily_digest


class DigestTests(unittest.TestCase):
    def test_generate_daily_digest_resume_notas_del_dia(self):
        now = datetime.now()
        notes = [
            {
                "id": "1",
                "type": "nota",
                "created_at": now.isoformat(),
                "metadata": {"enrichment": {"topics": ["investigacion"]}},
            },
            {
                "id": "2",
                "type": "recordatorio",
                "created_at": now.isoformat(),
                "metadata": {"enrichment": {"topics": ["agenda"]}},
            },
        ]

        digest = generate_daily_digest(notes, date_ref=now)
        self.assertEqual(digest["notes_count"], 2)
        self.assertEqual(digest["reminders_count"], 1)
        self.assertIn("investigacion", digest["top_topics"])
        self.assertIn("Digest del dia", digest["text"])


if __name__ == "__main__":
    unittest.main()
