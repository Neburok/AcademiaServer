import struct

import requests


class EmbeddingProvider:
    """Genera embeddings vectoriales usando el endpoint /api/embed de Ollama."""

    def __init__(self, base_url: str, embed_model: str, timeout_seconds: int = 25):
        self.base_url = base_url.rstrip("/")
        self.embed_model = embed_model
        self.timeout_seconds = timeout_seconds

    def generate(self, text: str) -> list[float] | None:
        """Genera embedding para el texto. Retorna None si Ollama no está disponible (degradación suave)."""
        try:
            url = f"{self.base_url}/api/embed"
            payload = {"model": self.embed_model, "input": text}
            response = requests.post(url, json=payload, timeout=self.timeout_seconds)
            response.raise_for_status()
            data = response.json()
            embeddings = data.get("embeddings")
            if embeddings and isinstance(embeddings, list) and embeddings[0]:
                return embeddings[0]
            return None
        except Exception:
            return None

    def to_bytes(self, vector: list[float]) -> bytes:
        """Serializa un vector float32 a bytes (little-endian)."""
        return struct.pack(f"<{len(vector)}f", *vector)

    def from_bytes(self, data: bytes) -> list[float]:
        """Deserializa bytes a vector float32."""
        n = len(data) // 4
        return list(struct.unpack(f"<{n}f", data))
