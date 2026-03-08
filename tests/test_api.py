import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from academiaserver.db.database import Base
from academiaserver.db import models  # noqa: F401 — registra Nota en Base
from academiaserver.db import database as db_module
from academiaserver import api


def _make_test_engine():
    # StaticPool garantiza que todas las sesiones comparten la misma conexión
    # en memoria, necesario para que los tests de FastAPI vean las tablas creadas.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


class ApiTests(unittest.TestCase):
    def setUp(self):
        self._engine = _make_test_engine()
        self._original_engine = db_module.engine
        self._original_session = db_module.SessionLocal
        db_module.engine = self._engine
        db_module.SessionLocal = sessionmaker(bind=self._engine, autoflush=False, autocommit=False)
        self.client = TestClient(api.app)

    def tearDown(self):
        db_module.engine = self._original_engine
        db_module.SessionLocal = self._original_session

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

    def test_list_retorna_lista_de_notas(self):
        self.client.post(
            "/save",
            json={"title": "Nota 1", "content": "Primera nota de prueba", "tags": []},
        )
        response = self.client.get("/list")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("ideas", data)
        self.assertEqual(len(data["ideas"]), 1)

    def test_idempotencia_no_duplica_contenido(self):
        body = {"title": "Test", "content": "Contenido identico para idempotencia", "tags": []}
        r1 = self.client.post("/save", json=body)
        r2 = self.client.post("/save", json=body)
        self.assertEqual(r1.json()["id"], r2.json()["id"])

        lista = self.client.get("/list").json()["ideas"]
        self.assertEqual(len(lista), 1)


if __name__ == "__main__":
    unittest.main()
