from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.session import get_db
from core.deps import get_current_user
from models.timeline import TimelineEvent
from schemas.timeline import TimelineEventRead

router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.get("/{patient_id}", response_model=list[TimelineEventRead])
def get_timeline(patient_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return (
        db.query(TimelineEvent)
        .filter(TimelineEvent.patient_id == patient_id)
        .order_by(TimelineEvent.event_time.desc())
        .limit(500)
        .all()
    )
