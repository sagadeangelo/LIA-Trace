
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import Settings


settings = Settings()

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """Clase base para los modelos de PostgreSQL."""

    pass


def get_db() -> Generator[Session, None, None]:
    """Proporciona una sesión de base de datos por solicitud."""

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
