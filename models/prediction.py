from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Float,
    JSON,
)
from sqlalchemy.orm import relationship

from db.base import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Model metadata
    model_name = Column(String(128), nullable=False, default="ckd_ci_model")
    model_version = Column(String(64), nullable=False, default="v1")

    # Prediction outputs
    predicted_label = Column(String(128), nullable=False)
    probabilities = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)

    # Raw input features used for this prediction (for traceability)
    input_features = Column(JSON, nullable=True)

    # `metadata` is a reserved attribute name on declarative base; map DB column 'metadata' to attribute `meta`
    meta = Column('metadata', JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    patient = relationship("Patient", back_populates="predictions")
    user = relationship("User", back_populates="predictions")

    def __repr__(self) -> str:  # pragma: no cover - convenience
        return f"<Prediction id={self.id} patient_id={self.patient_id} label={self.predicted_label}>"
