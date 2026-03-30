from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    JSON,
)

from db.base import Base
from sqlalchemy.orm import synonym


class ModelRegistry(Base):
    __tablename__ = "model_registry"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    version = Column(String(64), nullable=False)
    description = Column(String(255), nullable=True)
    artifact_path = Column(String(1024), nullable=True)
    # Map DB column 'metadata' to attribute `meta` kept for backward compat
    meta = Column('metadata', JSON, nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Compatibility aliases used by newer route code.
    model_name = synonym("name")
    metrics_json = synonym("meta")

    def __repr__(self) -> str:  # pragma: no cover - convenience
        return f"<ModelRegistry id={self.id} name={self.name} version={self.version}>"
