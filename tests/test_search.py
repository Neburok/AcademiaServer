import unittest

from academiaserver.search import SearchService


class SearchTests(unittest.TestCase):
    def test_keyword_search_encuentra_por_tema_enriquecido(self):
        notes = [
            {
                "id": "1",
                "title": "Nota SEM",
                "content": "Analisis de microscopia",
                "tags": [],
                "metadata": {"enrichment": {"topics": ["sem"]}},
            },
            {
                "id": "2",
                "title": "Docencia",
                "content": "Planeacion de clase",
                "tags": [],
                "metadata": {"enrichment": {"topics": ["docencia"]}},
            },
        ]

        service = SearchService(backend="keyword")
        results = service.search(notes, "sem")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "1")

    def test_semantic_backend_no_soportado_en_search_service(self):
        # La búsqueda semántica se maneja en core.search_ideas(), no en SearchService.
        # SearchService levanta ValueError si se solicita backend "semantic" directamente.
        with self.assertRaises(ValueError):
            SearchService(backend="semantic")


if __name__ == "__main__":
    unittest.main()
