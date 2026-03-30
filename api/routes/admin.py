from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from core.deps import require_role
from db.session import get_db
from models.audit_log import AuditLog
from models.prediction import Prediction

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/audit-logs", dependencies=[Depends(require_role("admin"))])
def list_audit_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> List[dict]:
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    return [{"id": l.id, "user_id": l.user_id, "action": l.action, "resource_type": l.resource_type, "resource_id": l.resource_id, "details": l.details, "created_at": l.created_at.isoformat()} for l in logs]


@router.get("/analytics", dependencies=[Depends(require_role("admin"))])
def analytics_summary(limit: int = 200, db: Session = Depends(get_db)) -> dict:
    preds = db.query(Prediction).order_by(Prediction.created_at.desc()).limit(limit).all()

    total_predictions = len(preds)
    class_distribution = {}
    confidence_sum = 0.0
    confidence_count = 0

    for p in preds:
        label = p.predicted_label or "unknown"
        class_distribution[label] = class_distribution.get(label, 0) + 1
        if p.confidence is not None:
            confidence_sum += float(p.confidence)
            confidence_count += 1

    avg_confidence = (confidence_sum / confidence_count) if confidence_count else 0.0

    model_avg_rows = (
        db.query(Prediction.model_version, func.avg(Prediction.confidence))
        .group_by(Prediction.model_version)
        .all()
    )
    avg_confidence_by_model_version = {
        str(model_version): float(avg_conf or 0.0)
        for model_version, avg_conf in model_avg_rows
    }

    latest_predictions = [
        {
            "id": p.id,
            "patient_id": p.patient_id,
            "model_version": p.model_version,
            "predicted_label": p.predicted_label,
            "confidence": p.confidence,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in preds[:20]
    ]

    return {
        "total_predictions": total_predictions,
        "class_distribution": class_distribution,
        "avg_confidence": avg_confidence,
        "avg_confidence_by_model_version": avg_confidence_by_model_version,
        "latest_predictions": latest_predictions,
    }
