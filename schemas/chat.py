from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ChatThreadBase(BaseModel):
    thread_type: str = "patient"
    patient_id: Optional[int] = None
    name: Optional[str] = None
    participants: Optional[List[int]] = None


class ChatThreadCreate(ChatThreadBase):
    pass


class ChatThreadRead(ChatThreadBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class ChatMessageBase(BaseModel):
    content: str


class ChatMessageCreate(ChatMessageBase):
    thread_id: int


class ChatMessageRead(ChatMessageBase):
    id: int
    thread_id: int
    sender_id: Optional[int] = None
    status: str
    created_at: datetime
    seen_at: Optional[datetime] = None

    class Config:
        orm_mode = True
