from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


class TimelineEventCreate(BaseModel):
    patient_id: int
    source_type: str
    source_id: Optional[int] = None
    summary: Optional[str] = None
    payload: Optional[dict[str, Any]] = None
    event_time: Optional[datetime] = None


class TimelineEventRead(TimelineEventCreate):
    id: int
    event_time: datetime

    class Config:
        orm_mode = True
