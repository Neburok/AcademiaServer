from datetime import datetime

from academiaserver.db import database as _db
from academiaserver.db import repository
from academiaserver.logger import log_event


def save_idea(data: dict) -> dict:
    if not data.get("content"):
        raise ValueError("La nota debe tener 'content'")

    db = _db.SessionLocal()
    try:
        data["id"] = repository.generate_id(db)
        data["created_at"] = datetime.now().isoformat()
        saved = repository.save_nota(db, data)
        log_event("nota_guardada", id=saved["id"], type=saved["type"])
        return saved
    finally:
        db.close()


def list_ideas() -> list[dict]:
    db = _db.SessionLocal()
    try:
        return repository.get_all(db)
    finally:
        db.close()


def get_idea(idea_id: str) -> dict | None:
    db = _db.SessionLocal()
    try:
        return repository.get_by_id(db, idea_id)
    finally:
        db.close()


def search_ideas(query: str) -> list[dict]:
    db = _db.SessionLocal()
    try:
        return repository.search_keyword(db, query)
    finally:
        db.close()


def get_pending_reminders(limit: int = 5) -> list[dict]:
    db = _db.SessionLocal()
    try:
        return repository.get_pending_reminders(db, limit=limit)
    finally:
        db.close()
