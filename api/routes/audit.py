from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.session import get_db
from core.deps import require_admin
from models.audit_log import AuditLog

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs")
def list_logs(limit: int = 200, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    entries = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [
        {
            "id": e.id,
            "user_id": e.user_id,
            "action": e.action,
            "resource_type": e.resource_type,
            "resource_id": e.resource_id,
            "details": e.details,
            "ip_address": e.ip_address,
            "created_at": e.created_at,
        }
        for e in entries
    ]
