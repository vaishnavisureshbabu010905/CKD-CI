from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship

from db.base import Base


class ChatThread(Base):
    __tablename__ = "chat_threads"

    id = Column(Integer, primary_key=True, index=True)
    thread_type = Column(String(32), default="patient", nullable=False)  # patient | team
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=True)
    participants = Column(JSON, nullable=True)  # list of user ids
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    patient = relationship("Patient")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("chat_threads.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    content = Column(Text, nullable=False)
    status = Column(String(32), default="sent", nullable=False)  # sent | delivered | seen
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    seen_at = Column(DateTime, nullable=True)

    thread = relationship("ChatThread")
    sender = relationship("User")
