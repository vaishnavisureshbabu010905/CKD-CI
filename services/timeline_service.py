from datetime import datetime
from typing import Optional, Any
from sqlalchemy.orm import Session

from models.timeline import TimelineEvent


def record_event(
    db: Session,
    *,
    patient_id: int,
    source_type: str,
    source_id: Optional[int] = None,
    summary: Optional[str] = None,
    payload: Optional[dict[str, Any]] = None,
    event_time: Optional[datetime] = None,
) -> TimelineEvent:
    entry = TimelineEvent(
        patient_id=patient_id,
        source_type=source_type,
        source_id=source_id,
        summary=summary,
        payload=payload or {},
        event_time=event_time or datetime.utcnow(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
