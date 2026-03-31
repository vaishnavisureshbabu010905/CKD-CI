from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


class AlertRuleBase(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_type: str
    condition: Optional[dict[str, Any]] = None
    severity: str = "medium"
    is_active: bool = True


class AlertRuleCreate(AlertRuleBase):
    pass


class AlertRuleRead(AlertRuleBase):
    id: int
    created_by: Optional[int] = None
    created_at: datetime

    class Config:
        orm_mode = True


class AlertEventBase(BaseModel):
    rule_id: Optional[int] = None
    patient_id: Optional[int] = None
    status: str = "open"
    payload: Optional[dict[str, Any]] = None


class AlertEventCreate(AlertEventBase):
    pass


class AlertEventRead(AlertEventBase):
    id: int
    triggered_by: Optional[int] = None
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[int] = None

    class Config:
        orm_mode = True
