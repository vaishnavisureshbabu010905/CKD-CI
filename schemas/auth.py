from typing import Optional
from pydantic import BaseModel

# Avoid requiring `email-validator` at import time in test environments
EmailStr = str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
