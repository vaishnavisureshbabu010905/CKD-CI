from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool

from config.settings import settings


# Create engine. In production, tune pool size appropriately or use
# a connection pool provided by the environment. We use pool_pre_ping
# to help avoid stale connections.
def _create_engine() -> Engine:
    # For simple local deployments, the default pool is sufficient. If you
    # prefer no pooling (e.g., serverless), switch to NullPool.
    return create_engine(
        settings.DATABASE_URL, pool_pre_ping=True, future=True
    )


engine = _create_engine()

SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, future=True
)


def get_db() -> Generator:
    """FastAPI dependency that yields a database session and ensures
    it is closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
