import hashlib
from datetime import datetime

from sqlalchemy.orm import Session

from academiaserver.db.models import Nota


def _to_dict(n: Nota) -> dict:
    d = {
        "id": n.id,
        "content": n.content,
        "title": n.title,
        "type": n.type,
        "source": n.source,
        "created_at": n.created_at,
        "tags": n.tags or [],
        "summary": n.summary or "",
        "priority": n.priority or "media",
    }
    if n.type == "recordatorio":
        d["reminder_datetime"] = n.reminder_datetime
        d["reminded"] = n.reminded
    return d


def generate_id(db: Session) -> str:
    today = datetime.now().strftime("%Y%m%d")
    count = db.query(Nota).filter(Nota.id.like(f"{today}-%")).count()
    return f"{today}-{count + 1:03d}"


def save_nota(db: Session, data: dict) -> dict:
    content_hash = hashlib.sha256(data["content"].encode()).hexdigest()
    existing = db.query(Nota).filter_by(content_hash=content_hash).first()
    if existing:
        return _to_dict(existing)

    nota = Nota(
        id=data["id"],
        content=data["content"],
        title=data.get("title"),
        type=data.get("type", "nota"),
        source=data.get("source", "telegram"),
        content_hash=content_hash,
        created_at=data.get("created_at", datetime.now().isoformat()),
        tags=data.get("tags", []),
        summary=data.get("summary", ""),
        priority=data.get("priority", "media"),
        reminder_datetime=data.get("reminder_datetime"),
        reminded=data.get("reminded", False),
    )
    db.add(nota)
    db.commit()
    db.refresh(nota)
    return _to_dict(nota)


def get_all(db: Session) -> list[dict]:
    notas = db.query(Nota).order_by(Nota.created_at.desc()).all()
    return [_to_dict(n) for n in notas]


def get_by_id(db: Session, nota_id: str) -> dict | None:
    n = db.query(Nota).filter_by(id=nota_id).first()
    return _to_dict(n) if n else None


def search_keyword(db: Session, query: str) -> list[dict]:
    q = query.lower().strip()
    if not q:
        return []
    results = []
    for n in db.query(Nota).all():
        haystack = " ".join([
            n.title or "", n.content or "", " ".join(n.tags or [])
        ]).lower()
        if q in haystack:
            results.append(_to_dict(n))
    return results


def get_due_reminders(db: Session) -> list[dict]:
    now = datetime.now()
    notas = db.query(Nota).filter(
        Nota.type == "recordatorio",
        Nota.reminded == False,  # noqa: E712
        Nota.reminder_datetime.isnot(None),
    ).all()
    results = []
    for n in notas:
        try:
            if datetime.fromisoformat(n.reminder_datetime) <= now:
                results.append(_to_dict(n))
        except (ValueError, TypeError):
            pass
    return results


def get_pending_reminders(db: Session, limit: int = 5) -> list[dict]:
    notas = db.query(Nota).filter(
        Nota.type == "recordatorio",
        Nota.reminded == False,  # noqa: E712
        Nota.reminder_datetime.isnot(None),
    ).order_by(Nota.reminder_datetime).limit(limit).all()
    return [_to_dict(n) for n in notas]


def mark_as_reminded(db: Session, nota_id: str):
    n = db.query(Nota).filter_by(id=nota_id).first()
    if n:
        n.reminded = True
        db.commit()
