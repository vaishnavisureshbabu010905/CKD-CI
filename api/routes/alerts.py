from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.session import get_db
from core.deps import get_current_user, require_admin, require_doctor_or_admin
from models.alert import AlertRule, AlertEvent
from schemas.alert import AlertRuleCreate, AlertRuleRead, AlertEventCreate, AlertEventRead
from services.audit_service import log_audit
from services.timeline_service import record_event

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("/rules", response_model=AlertRuleRead)
def create_rule(payload: AlertRuleCreate, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    rule = AlertRule(
        name=payload.name,
        description=payload.description,
        trigger_type=payload.trigger_type,
        condition=payload.condition,
        severity=payload.severity,
        is_active=payload.is_active,
        created_by=current_user.id,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    log_audit(db, current_user, action="create_alert_rule", resource_type="alert_rule", resource_id=str(rule.id))
    return rule


@router.get("/rules", response_model=list[AlertRuleRead])
def list_rules(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(AlertRule).order_by(AlertRule.created_at.desc()).all()


@router.post("/events", response_model=AlertEventRead)
def create_event(payload: AlertEventCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    event = AlertEvent(
        rule_id=payload.rule_id,
        patient_id=payload.patient_id,
        triggered_by=current_user.id,
        status=payload.status,
        payload=payload.payload,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    if event.patient_id:
        record_event(
            db,
            patient_id=event.patient_id,
            source_type="alert",
            source_id=event.id,
            summary=f"Alert triggered ({event.status})",
            payload=payload.payload,
        )
    log_audit(db, current_user, action="alert_trigger", resource_type="alert_event", resource_id=str(event.id))
    return event


@router.post("/events/{event_id}/ack", response_model=AlertEventRead)
def acknowledge_event(event_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    event = db.query(AlertEvent).filter(AlertEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert event not found")
    event.status = "acknowledged"
    event.acknowledged_by = current_user.id
    from datetime import datetime
    event.acknowledged_at = datetime.utcnow()
    db.add(event)
    db.commit()
    db.refresh(event)
    log_audit(db, current_user, action="alert_ack", resource_type="alert_event", resource_id=str(event.id))
    return event


@router.post("/events/{event_id}/resolve", response_model=AlertEventRead)
def resolve_event(event_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    event = db.query(AlertEvent).filter(AlertEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert event not found")
    event.status = "resolved"
    db.add(event)
    db.commit()
    db.refresh(event)
    log_audit(db, current_user, action="alert_resolve", resource_type="alert_event", resource_id=str(event.id))
    return event


@router.get("/events", response_model=list[AlertEventRead])
def list_events(patient_id: int | None = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    q = db.query(AlertEvent).order_by(AlertEvent.created_at.desc())
    if patient_id:
        q = q.filter(AlertEvent.patient_id == patient_id)
    return q.limit(200).all()
