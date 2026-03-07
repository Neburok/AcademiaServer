from academiaserver.search.base import SearchEngine
from academiaserver.search.keyword import KeywordSearchEngine


class SemanticSearchEngine(SearchEngine):
    def search(self, notes: list[dict], query: str) -> list[dict]:
        raise NotImplementedError(
            "Busqueda semantica no implementada todavia. Usa backend='keyword'."
        )


class SearchService:
    def __init__(self, backend: str = "keyword"):
        self.backend = backend
        self.engine = self._build_engine(backend)

    def _build_engine(self, backend: str) -> SearchEngine:
        if backend == "keyword":
            return KeywordSearchEngine()
        if backend == "semantic":
            return SemanticSearchEngine()
        raise ValueError(f"Backend de busqueda no soportado: {backend}")

    def search(self, notes: list[dict], query: str) -> list[dict]:
        return self.engine.search(notes, query)
