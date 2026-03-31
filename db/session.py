from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine

from config.settings import settings


def _create_engine() -> Engine:
    """Create the SQLAlchemy engine with sensible defaults.

    For local/dev we use a small pool; production can override via envs.
    """
    return create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        future=True,
        echo=settings.DB_ECHO,
        pool_size=settings.DB_POOL_SIZE if "sqlite" not in settings.DATABASE_URL else None,
        max_overflow=settings.DB_MAX_OVERFLOW if "sqlite" not in settings.DATABASE_URL else None,
    )


engine = _create_engine()

SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, future=True
)


def get_db() -> Generator:
    """FastAPI dependency that yields a database session and ensures it is closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
