from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship

from db.base import Base


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(512), nullable=True)
    trigger_type = Column(String(64), nullable=False)  # e.g., prediction_high_risk, lab_delta
    condition = Column(JSON, nullable=True)  # rule config payload
    severity = Column(String(32), nullable=False, default="medium")
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    creator = relationship("User")


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("alert_rules.id", ondelete="SET NULL"), nullable=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="SET NULL"), nullable=True)
    triggered_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(32), default="open", nullable=False)  # open | acknowledged | escalated | resolved
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    rule = relationship("AlertRule")
    patient = relationship("Patient")
    triggered_by_user = relationship("User", foreign_keys=[triggered_by])
    acknowledged_by_user = relationship("User", foreign_keys=[acknowledged_by])
