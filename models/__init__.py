"""
Models module - all SQLAlchemy models are imported here to ensure proper registration
and relationship resolution.
"""

# Import all models in proper order (base classes first, then dependent models)
from models.user import User
from models.patient import Patient
from models.prediction import Prediction
from models.model_registry import ModelRegistry
from models.audit_log import AuditLog
from models.alert import AlertRule, AlertEvent
from models.note import Note, Task
from models.chat import ChatThread, ChatMessage
from models.timeline import TimelineEvent

__all__ = [
    "User",
    "Patient",
    "Prediction",
    "ModelRegistry",
    "AuditLog",
    "AlertRule",
    "AlertEvent",
    "Note",
    "Task",
    "ChatThread",
    "ChatMessage",
    "TimelineEvent",
]
