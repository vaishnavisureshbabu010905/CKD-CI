from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.session import get_db
from core.deps import get_current_user, require_role
from schemas.user import UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_current_user(current_user=Depends(get_current_user)):
    return current_user


@router.get("/", dependencies=[Depends(require_role("admin"))])
def list_users(db: Session = Depends(get_db)):
    users = db.query("User").all()  # placeholder - replace with proper query if needed
    return {"count": len(users)}
