from academiaserver.search.base import SearchEngine
from academiaserver.search.keyword import KeywordSearchEngine


class SearchService:
    def __init__(self, backend: str = "keyword"):
        self.backend = backend
        self.engine = self._build_engine(backend)

    def _build_engine(self, backend: str) -> SearchEngine:
        if backend == "keyword":
            return KeywordSearchEngine()
        raise ValueError(f"Backend de busqueda no soportado: {backend}")

    def search(self, notes: list[dict], query: str) -> list[dict]:
        return self.engine.search(notes, query)
