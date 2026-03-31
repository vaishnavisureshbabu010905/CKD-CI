from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from db.base import Base


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    source_type = Column(String(64), nullable=False)  # prediction | alert | note | task | chat | encounter
    source_id = Column(Integer, nullable=True)
    event_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    summary = Column(String(255), nullable=True)
    payload = Column(JSON, nullable=True)

    patient = relationship("Patient")
