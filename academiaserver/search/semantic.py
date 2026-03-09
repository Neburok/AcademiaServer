import math

from academiaserver.ai.embedding_provider import EmbeddingProvider


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Similitud coseno entre dos vectores. Retorna valor en [-1, 1]."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class SemanticSearchEngine:
    """Búsqueda semántica por similitud de embeddings vectoriales."""

    def __init__(self, embedding_provider: EmbeddingProvider):
        self.embedding_provider = embedding_provider

    def search(
        self,
        notes_with_embeddings: list[tuple[dict, bytes]],
        query: str,
        top_k: int = 10,
        min_score: float = 0.0,
    ) -> list[dict]:
        """
        Busca las notas más similares semánticamente a la query.

        - min_score: umbral mínimo de similitud coseno (0.0 = sin filtro,
          0.60 = solo conexiones claras, útil para Fase 4 — conexiones automáticas).
        - Si Ollama no está disponible para generar el embedding de la query,
          retorna lista vacía (degradación suave).
        """
        query_vector = self.embedding_provider.generate(query)
        if query_vector is None:
            return []

        scored = []
        for nota_dict, embedding_bytes in notes_with_embeddings:
            nota_vector = self.embedding_provider.from_bytes(embedding_bytes)
            score = cosine_similarity(query_vector, nota_vector)
            if score >= min_score:
                scored.append((score, nota_dict))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [nota for _, nota in scored[:top_k]]
