import os
import shutil
import tempfile
import unittest

from fastapi.testclient import TestClient

from academiaserver import api, config, core


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="academiaserver_api_test_")
        self.original_config_inbox = config.INBOX_DIR
        self.original_core_inbox = core.INBOX_DIR
        config.INBOX_DIR = self.temp_dir
        core.INBOX_DIR = self.temp_dir
        self.client = TestClient(api.app)

    def tearDown(self):
        config.INBOX_DIR = self.original_config_inbox
        core.INBOX_DIR = self.original_core_inbox
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_crea_nota_con_esquema_compatible(self):
        response = self.client.post(
            "/save",
            json={
                "title": "Titulo de prueba",
                "content": "Contenido de prueba",
                "tags": ["test"],
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("id", payload)
        self.assertEqual(payload["title"], "Titulo de prueba")
        self.assertEqual(payload["source"], "api")
        self.assertEqual(payload["schema_version"], "1.0.0")
        self.assertIn("enrichment", payload["metadata"])
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, f"{payload['id']}.json")))


if __name__ == "__main__":
    unittest.main()
