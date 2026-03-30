from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from db.base import Base


class Patient(Base):
    __tablename__ = "patients"
    __table_args__ = (UniqueConstraint("patient_identifier", name="uq_patient_identifier"),)

    id = Column(Integer, primary_key=True, index=True)
    patient_identifier = Column(String(128), nullable=False)
    first_name = Column(String(128), nullable=True)
    last_name = Column(String(128), nullable=True)
    date_of_birth = Column(String(32), nullable=True)
    sex = Column(String(16), nullable=True)

    # Store the raw clinical feature set as JSON for traceability and
    # re-scoring. Keep canonical feature columns in the prediction
    # service for model input ordering.
    features = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    predictions = relationship("Prediction", back_populates="patient", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover - convenience
        return f"<Patient id={self.id} pid={self.patient_identifier}>"
