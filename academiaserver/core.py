from datetime import datetime

from academiaserver.ai.embedding_provider import EmbeddingProvider
from academiaserver.config import AI_TIMEOUT_SECONDS, OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL
from academiaserver.db import database as _db
from academiaserver.db import repository
from academiaserver.digest import generate_daily_digest
from academiaserver.events.bus import bus
from academiaserver.logger import log_event
from academiaserver.schemas import canonicalize_note
from academiaserver.search import SearchService
from academiaserver.search.semantic import SemanticSearchEngine

_embedding_provider = EmbeddingProvider(
    base_url=OLLAMA_BASE_URL,
    embed_model=OLLAMA_EMBED_MODEL,
    timeout_seconds=AI_TIMEOUT_SECONDS,
)


def save_idea(note: dict) -> dict:
    if "content" not in note:
        raise ValueError("La nota debe contener 'content'")

    note = canonicalize_note(note)

    db = _db.SessionLocal()
    try:
        note["id"] = repository.generate_id(db)
        note["created_at"] = datetime.now().isoformat()
        saved = repository.save_nota(db, note)
    finally:
        db.close()

    # Generar y almacenar embedding (degradación suave si Ollama no está disponible)
    embedding = _embedding_provider.generate(note.get("content", ""))
    if embedding:
        db = _db.SessionLocal()
        try:
            repository.update_embedding(db, saved["id"], _embedding_provider.to_bytes(embedding))
        finally:
            db.close()

    bus.publish("nota.guardada", {"id": saved["id"], "type": saved["type"]})
    return saved


def list_ideas() -> list[dict]:
    db = _db.SessionLocal()
    try:
        return repository.get_all_notas(db)
    finally:
        db.close()


def load_all_ideas() -> list[dict]:
    return list_ideas()


def get_idea_by_id(idea_id: str) -> dict | None:
    db = _db.SessionLocal()
    try:
        return repository.get_nota_by_id(db, idea_id)
    finally:
        db.close()


def search_ideas(query: str, backend: str = "keyword") -> list[dict]:
    if backend == "semantic":
        db = _db.SessionLocal()
        try:
            notes_with_embeddings = repository.get_all_with_embeddings(db)
        finally:
            db.close()
        engine = SemanticSearchEngine(_embedding_provider)
        return engine.search(notes_with_embeddings, query)

    ideas = load_all_ideas()
    service = SearchService(backend=backend)
    return service.search(ideas, query)


def get_daily_digest() -> dict:
    ideas = load_all_ideas()
    return generate_daily_digest(ideas)


def reembed_notas() -> dict:
    """Genera embeddings para todas las notas que no tienen uno. Retorna estadísticas."""
    db = _db.SessionLocal()
    try:
        pendientes = repository.get_notas_sin_embedding(db)
    finally:
        db.close()

    total = len(pendientes)
    procesadas = 0
    fallidas = 0

    for nota in pendientes:
        embedding = _embedding_provider.generate(nota["content"])
        if embedding:
            db = _db.SessionLocal()
            try:
                repository.update_embedding(
                    db, nota["id"], _embedding_provider.to_bytes(embedding)
                )
            finally:
                db.close()
            procesadas += 1
        else:
            fallidas += 1

    return {"total": total, "procesadas": procesadas, "fallidas": fallidas}


def get_memory_context(query: str, top_k: int = 3) -> list[dict]:
    """Busca las notas más relevantes semánticamente para usar como memoria activa."""
    db = _db.SessionLocal()
    try:
        notes_with_embeddings = repository.get_all_with_embeddings(db)
    finally:
        db.close()

    if not notes_with_embeddings:
        return []

    engine = SemanticSearchEngine(_embedding_provider)
    return engine.search(notes_with_embeddings, query, top_k=top_k)
