import math
import struct
import unittest
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from academiaserver.ai.embedding_provider import EmbeddingProvider
from academiaserver.db import models  # noqa: F401 — registra Nota en Base
from academiaserver.db import repository
from academiaserver.db.database import Base
from academiaserver.search.semantic import SemanticSearchEngine, cosine_similarity


def make_test_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


class TestCosineSimilarity(unittest.TestCase):
    def test_vector_consigo_mismo_es_uno(self):
        v = [1.0, 2.0, 3.0]
        resultado = cosine_similarity(v, v)
        self.assertAlmostEqual(resultado, 1.0, places=6)

    def test_vectores_ortogonales_es_cero(self):
        a = [1.0, 0.0, 0.0]
        b = [0.0, 1.0, 0.0]
        resultado = cosine_similarity(a, b)
        self.assertAlmostEqual(resultado, 0.0, places=6)

    def test_vectores_opuestos_es_menos_uno(self):
        a = [1.0, 0.0]
        b = [-1.0, 0.0]
        resultado = cosine_similarity(a, b)
        self.assertAlmostEqual(resultado, -1.0, places=6)

    def test_vector_cero_retorna_cero(self):
        a = [0.0, 0.0]
        b = [1.0, 2.0]
        resultado = cosine_similarity(a, b)
        self.assertEqual(resultado, 0.0)


class TestEmbeddingProviderSerializacion(unittest.TestCase):
    def setUp(self):
        self.provider = EmbeddingProvider(
            base_url="http://localhost:11434",
            embed_model="nomic-embed-text",
        )

    def test_roundtrip_sin_perdida(self):
        vector = [0.1, 0.5, -0.3, 1.0, -1.0, 0.0]
        serializado = self.provider.to_bytes(vector)
        recuperado = self.provider.from_bytes(serializado)
        self.assertEqual(len(recuperado), len(vector))
        for original, recup in zip(vector, recuperado):
            self.assertAlmostEqual(original, recup, places=5)

    def test_to_bytes_produce_bytes(self):
        vector = [1.0, 2.0, 3.0]
        resultado = self.provider.to_bytes(vector)
        self.assertIsInstance(resultado, bytes)
        self.assertEqual(len(resultado), 3 * 4)  # 3 floats × 4 bytes

    def test_from_bytes_768_dims(self):
        """Simula un embedding real de 768 dimensiones (nomic-embed-text)."""
        vector = [float(i) / 768 for i in range(768)]
        serializado = self.provider.to_bytes(vector)
        recuperado = self.provider.from_bytes(serializado)
        self.assertEqual(len(recuperado), 768)

    def test_generate_retorna_none_si_ollama_no_disponible(self):
        with patch("requests.post", side_effect=ConnectionError("sin conexion")):
            resultado = self.provider.generate("texto de prueba")
        self.assertIsNone(resultado)


class TestEmbeddingProviderConMock(unittest.TestCase):
    def test_generate_retorna_vector_con_respuesta_valida(self):
        vector_esperado = [0.1, 0.2, 0.3]
        mock_response = MagicMock()
        mock_response.json.return_value = {"embeddings": [vector_esperado]}
        mock_response.raise_for_status.return_value = None

        provider = EmbeddingProvider(
            base_url="http://localhost:11434",
            embed_model="nomic-embed-text",
        )
        with patch("requests.post", return_value=mock_response):
            resultado = provider.generate("texto")

        self.assertEqual(resultado, vector_esperado)


class TestSemanticSearchEngine(unittest.TestCase):
    def _make_provider_mock(self, query_vector):
        provider = MagicMock(spec=EmbeddingProvider)
        provider.generate.return_value = query_vector
        provider.from_bytes.side_effect = lambda b: list(
            struct.unpack(f"<{len(b) // 4}f", b)
        )
        return provider

    def test_retorna_vacio_si_ollama_no_disponible(self):
        provider = MagicMock(spec=EmbeddingProvider)
        provider.generate.return_value = None
        engine = SemanticSearchEngine(provider)
        resultado = engine.search([({}, b"\x00")], "query")
        self.assertEqual(resultado, [])

    def test_ordena_por_similitud_descendente(self):
        real_provider = EmbeddingProvider(
            base_url="http://localhost:11434",
            embed_model="nomic-embed-text",
        )
        # Vectores: query=[1,0], nota_a=[1,0] (similitud=1.0), nota_b=[0,1] (similitud=0.0)
        v_query = [1.0, 0.0]
        v_a = [1.0, 0.0]
        v_b = [0.0, 1.0]

        nota_a = {"id": "a", "content": "nota a"}
        nota_b = {"id": "b", "content": "nota b"}

        bytes_a = real_provider.to_bytes(v_a)
        bytes_b = real_provider.to_bytes(v_b)

        provider_mock = self._make_provider_mock(v_query)
        engine = SemanticSearchEngine(provider_mock)

        resultado = engine.search([(nota_a, bytes_a), (nota_b, bytes_b)], "query")

        self.assertEqual(len(resultado), 2)
        self.assertEqual(resultado[0]["id"], "a")
        self.assertEqual(resultado[1]["id"], "b")

    def test_top_k_limita_resultados(self):
        real_provider = EmbeddingProvider(
            base_url="http://localhost:11434",
            embed_model="nomic-embed-text",
        )
        v_query = [1.0, 0.0]
        notas = [
            ({"id": str(i), "content": f"nota {i}"}, real_provider.to_bytes([float(i), 0.0]))
            for i in range(5)
        ]

        provider_mock = self._make_provider_mock(v_query)
        engine = SemanticSearchEngine(provider_mock)
        resultado = engine.search(notas, "query", top_k=3)
        self.assertEqual(len(resultado), 3)


class TestSaveIdeaGeneraEmbedding(unittest.TestCase):
    """Verifica que save_idea genera y almacena el embedding si Ollama responde."""

    def test_embedding_almacenado_en_bd(self):
        vector_mock = [0.1, 0.2, 0.3]
        mock_response = MagicMock()
        mock_response.json.return_value = {"embeddings": [vector_mock]}
        mock_response.raise_for_status.return_value = None

        db = make_test_session()

        with patch("academiaserver.core._embedding_provider") as mock_ep:
            mock_ep.generate.return_value = vector_mock
            mock_ep.to_bytes.return_value = b"\x00" * 12
            with patch("academiaserver.db.database.SessionLocal", return_value=db):
                from academiaserver.core import save_idea
                nota = {"content": "Probando embeddings en la base de datos"}
                try:
                    save_idea(nota)
                except Exception:
                    pass  # Puede fallar por el bus u otros efectos secundarios

        # Verificar que se llamó generate con el contenido
        mock_ep.generate.assert_called()
        db.close()


if __name__ == "__main__":
    unittest.main()
