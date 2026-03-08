import hashlib
from datetime import datetime

from sqlalchemy.orm import Session

from academiaserver.db.models import Nota


def _nota_to_dict(n: Nota) -> dict:
    """Convierte un ORM Nota al formato dict canónico esperado por el resto del sistema."""
    d = {
        "id": n.id,
        "content": n.content,
        "title": n.title,
        "type": n.type,
        "source": n.source,
        "schema_version": n.schema_version,
        "created_at": n.created_at,
        "tags": n.tags or [],
        "links": n.links or [],
        "metadata": {
            "enrichment": {
                "topics": n.topics or [],
                "priority": n.priority or "baja",
                "summary": n.summary or "",
                "entities": n.entities or [],
            },
        },
    }
    if n.type == "recordatorio":
        d["metadata"]["datetime"] = n.reminder_datetime
        d["metadata"]["reminded"] = n.reminded
    return d


def save_nota(db: Session, nota_dict: dict) -> dict:
    """Guarda una nota. Si ya existe el mismo contenido (hash), retorna la existente (idempotencia)."""
    content_hash = hashlib.sha256(nota_dict["content"].encode()).hexdigest()

    existing = db.query(Nota).filter_by(content_hash=content_hash).first()
    if existing:
        return _nota_to_dict(existing)

    metadata = nota_dict.get("metadata", {})
    enrichment = metadata.get("enrichment", {})

    nota = Nota(
        id=nota_dict["id"],
        content=nota_dict["content"],
        title=nota_dict.get("title"),
        type=nota_dict.get("type", "nota"),
        source=nota_dict.get("source", "unknown"),
        schema_version=nota_dict.get("schema_version", "1.0.0"),
        content_hash=content_hash,
        created_at=nota_dict.get("created_at", datetime.now().isoformat()),
        tags=nota_dict.get("tags", []),
        links=nota_dict.get("links", []),
        topics=enrichment.get("topics", []),
        priority=enrichment.get("priority", "baja"),
        summary=enrichment.get("summary", ""),
        entities=enrichment.get("entities", []),
        reminder_datetime=metadata.get("datetime"),
        reminded=metadata.get("reminded", False),
    )

    db.add(nota)
    db.commit()
    db.refresh(nota)
    return _nota_to_dict(nota)


def get_all_notas(db: Session) -> list[dict]:
    notas = db.query(Nota).order_by(Nota.created_at).all()
    return [_nota_to_dict(n) for n in notas]


def get_nota_by_id(db: Session, nota_id: str) -> dict | None:
    nota = db.query(Nota).filter_by(id=nota_id).first()
    return _nota_to_dict(nota) if nota else None


def get_due_reminders(db: Session) -> list[dict]:
    """Retorna recordatorios vencidos y no enviados."""
    now = datetime.now()
    notas = (
        db.query(Nota)
        .filter(
            Nota.type == "recordatorio",
            Nota.reminded == False,  # noqa: E712
            Nota.reminder_datetime.isnot(None),
        )
        .all()
    )
    results = []
    for n in notas:
        try:
            if datetime.fromisoformat(n.reminder_datetime) <= now:
                results.append(_nota_to_dict(n))
        except (ValueError, TypeError):
            pass
    return results


def get_pending_reminders(db: Session, limit: int = 5) -> list[dict]:
    """Retorna los próximos recordatorios pendientes (no enviados), ordenados por fecha."""
    notas = (
        db.query(Nota)
        .filter(
            Nota.type == "recordatorio",
            Nota.reminded == False,  # noqa: E712
            Nota.reminder_datetime.isnot(None),
        )
        .order_by(Nota.reminder_datetime)
        .limit(limit)
        .all()
    )
    return [_nota_to_dict(n) for n in notas]


def mark_as_reminded(db: Session, nota_id: str):
    nota = db.query(Nota).filter_by(id=nota_id).first()
    if nota:
        nota.reminded = True
        db.commit()


def search_by_keyword(db: Session, query: str) -> list[dict]:
    normalized = query.lower().strip()
    if not normalized:
        return []
    notas = db.query(Nota).all()
    results = []
    for n in notas:
        haystack = " ".join([
            str(n.title or ""),
            str(n.content or ""),
            " ".join(n.tags or []),
            " ".join(n.topics or []),
        ]).lower()
        if normalized in haystack:
            results.append(_nota_to_dict(n))
    return results


def generate_id(db: Session) -> str:
    """Genera un ID único para la nota del día, estilo YYYYMMDD-NNN."""
    today = datetime.now().strftime("%Y%m%d")
    count = db.query(Nota).filter(Nota.id.like(f"{today}-%")).count()
    return f"{today}-{count + 1:03d}"


def update_embedding(db: Session, nota_id: str, embedding_bytes: bytes):
    """Guarda el embedding vectorial de una nota."""
    nota = db.query(Nota).filter_by(id=nota_id).first()
    if nota:
        nota.embedding = embedding_bytes
        db.commit()


def get_all_with_embeddings(db: Session) -> list[tuple[dict, bytes]]:
    """Retorna todas las notas que tienen embedding, como lista de (dict, bytes)."""
    notas = db.query(Nota).filter(Nota.embedding.isnot(None)).all()
    return [(_nota_to_dict(n), n.embedding) for n in notas]


def get_notas_sin_embedding(db: Session) -> list[dict]:
    """Retorna todas las notas que aún no tienen embedding generado."""
    notas = db.query(Nota).filter(Nota.embedding.is_(None)).all()
    return [_nota_to_dict(n) for n in notas]
