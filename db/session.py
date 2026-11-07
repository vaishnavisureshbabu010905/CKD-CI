from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine

from config.settings import settings


def _create_engine() -> Engine:
    """Create the SQLAlchemy engine with sensible defaults.

    For local/dev we use a small pool; production can override via envs.
    """
    kwargs = {
        "echo": settings.DB_ECHO,
        "future": True,
    }
    if "sqlite" in settings.DATABASE_URL:
        from sqlalchemy.pool import StaticPool
        kwargs["connect_args"] = {"check_same_thread": False}
        if ":memory:" in settings.DATABASE_URL:
            kwargs["poolclass"] = StaticPool
    else:
        kwargs["pool_pre_ping"] = True
        kwargs["pool_size"] = settings.DB_POOL_SIZE
        kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW

    return create_engine(settings.DATABASE_URL, **kwargs)


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
