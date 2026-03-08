from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from academiaserver.config import DB_PATH

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
    echo=False,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def init_db():
    """Crea las tablas si no existen. Usar solo en tests o desarrollo inicial."""
    from academiaserver.db import models  # noqa: F401 — necesario para registrar el modelo
    Base.metadata.create_all(engine)
