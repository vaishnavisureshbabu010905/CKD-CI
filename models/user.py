from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship

from db.base import Base


class UserRole:
    ADMIN = "admin"
    DOCTOR = "doctor"
    LAB = "lab_technician"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(512), nullable=False)
    role = Column(
        SAEnum(UserRole.ADMIN, UserRole.DOCTOR, UserRole.LAB, name="user_roles"),
        nullable=False,
        server_default=UserRole.DOCTOR,
    )
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    predictions = relationship("Prediction", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover - convenience method
        return f"<User id={self.id} email={self.email} role={self.role}>"
