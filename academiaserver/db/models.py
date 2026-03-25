from sqlalchemy import Boolean, Column, String, Text
from sqlalchemy.types import JSON

from academiaserver.db.database import Base


class Nota(Base):
    __tablename__ = "notas"

    id = Column(String, primary_key=True)
    content = Column(Text, nullable=False)
    title = Column(String)
    type = Column(String, default="nota")           # "nota" | "recordatorio" | "pregunta"
    source = Column(String, default="telegram")
    content_hash = Column(String, index=True)       # SHA-256 para idempotencia
    created_at = Column(String, nullable=False)
    tags = Column(JSON, default=list)
    summary = Column(Text)
    priority = Column(String, default="media")
    reminder_datetime = Column(String)              # solo recordatorios
    reminded = Column(Boolean, default=False)
