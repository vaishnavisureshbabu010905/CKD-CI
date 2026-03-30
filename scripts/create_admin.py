"""Create an admin user from environment variables.

Reads ADMIN_EMAIL and ADMIN_PASSWORD from environment or .env file and
creates an admin user if one does not already exist.
"""
from __future__ import annotations
import os
import sys
from dotenv import load_dotenv
from sqlalchemy.orm import Session

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from db.session import SessionLocal
from models.user import User
from models.patient import Patient  # noqa: F401 - ensures mapper registry is complete
from models.prediction import Prediction  # noqa: F401 - ensures mapper registry is complete
from models.audit_log import AuditLog  # noqa: F401 - ensures mapper registry is complete
from core.security import get_password_hash


load_dotenv()


def create_admin(email: str, password: str) -> None:
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            print(f"Admin user already exists: {email}")
            return

        hashed = get_password_hash(password)
        admin = User(email=email, full_name="Administrator", hashed_password=hashed, role="admin")
        db.add(admin)
        db.commit()
        print(f"Created admin user: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        print("Please set ADMIN_EMAIL and ADMIN_PASSWORD in environment or .env")
        raise SystemExit(1)
    create_admin(ADMIN_EMAIL, ADMIN_PASSWORD)
