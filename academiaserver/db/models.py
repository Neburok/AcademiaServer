from sqlalchemy import Boolean, Column, LargeBinary, String, Text
from sqlalchemy.types import JSON

from academiaserver.db.database import Base


class Nota(Base):
    __tablename__ = "notas"

    id = Column(String, primary_key=True)
    content = Column(Text, nullable=False)
    title = Column(String)
    type = Column(String, default="nota")           # "nota" | "recordatorio"
    source = Column(String, default="unknown")
    schema_version = Column(String, default="1.0.0")
    content_hash = Column(String, index=True)       # SHA-256 para idempotencia
    created_at = Column(String, nullable=False)
    tags = Column(JSON, default=list)
    links = Column(JSON, default=list)
    topics = Column(JSON, default=list)             # metadata.enrichment.topics
    priority = Column(String, default="baja")       # metadata.enrichment.priority
    summary = Column(Text)                          # metadata.enrichment.summary
    entities = Column(JSON, default=list)           # metadata.enrichment.entities
    reminder_datetime = Column(String)              # metadata.datetime (solo recordatorios)
    reminded = Column(Boolean, default=False)       # metadata.reminded
    embedding = Column(LargeBinary)                 # Vector float32 (Fase 3)
