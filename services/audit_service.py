from typing import Any, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from models.audit_log import AuditLog


def log_audit(db: Session, user: Optional[Any], action: str, resource_type: str = None, resource_id: str = None, details: dict = None, ip_address: str = None) -> AuditLog:
    entry = AuditLog(
        user_id=getattr(user, "id", None),
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        ip_address=ip_address,
        created_at=datetime.utcnow(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
