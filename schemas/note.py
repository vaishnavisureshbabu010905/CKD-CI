from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class NoteBase(BaseModel):
    patient_id: int
    encounter_id: Optional[int] = None
    note_type: str = "clinical"
    content: str


class NoteCreate(NoteBase):
    pass


class NoteRead(NoteBase):
    id: int
    author_id: Optional[int] = None
    created_at: datetime

    class Config:
        orm_mode = True


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    patient_id: Optional[int] = None
    status: str = "open"
    priority: str = "normal"
    due_at: Optional[datetime] = None
    assignee_id: Optional[int] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[int] = None
    due_at: Optional[datetime] = None
    title: Optional[str] = None
    description: Optional[str] = None


class TaskRead(TaskBase):
    id: int
    created_by: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        orm_mode = True
