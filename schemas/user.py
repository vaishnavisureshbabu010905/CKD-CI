from typing import Optional
from pydantic import BaseModel

# Avoid requiring `email-validator` at import time in test environments
EmailStr = str


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str
    role: Optional[str] = "doctor"


class UserRead(UserBase):
    id: int
    role: str
    is_active: bool

    class Config:
        orm_mode = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
