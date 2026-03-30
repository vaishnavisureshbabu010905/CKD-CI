from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from db.session import get_db
from core.security import decode_access_token
from models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = decode_access_token(token)
        email: Optional[str] = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_role(role: str):
    def _role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = str(current_user.role or "").strip().lower()
        wanted = str(role or "").strip().lower()
        if user_role == "lab_technician":
            user_role = "nurse"
        if wanted == "lab_technician":
            wanted = "nurse"

        if user_role != wanted and user_role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges")
        return current_user

    return _role_checker


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return current_user


def require_doctor_or_admin(current_user: User = Depends(get_current_user)) -> User:
    role = str(current_user.role or "").strip().lower()
    if role == "lab_technician":
        role = "nurse"
    if role not in ("doctor", "nurse", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Doctor, nurse, or admin privileges required")
    return current_user
