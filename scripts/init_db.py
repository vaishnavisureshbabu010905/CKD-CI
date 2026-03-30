"""Database initialization helper.

Creates tables and optional seed data. Safe to run multiple times.
"""
from __future__ import annotations
from typing import Optional
from db.base import Base
from db.session import engine
from sqlalchemy import text


def init_db(seed: bool = False) -> None:
    """Create all tables and optionally add seed data.

    Safe to run multiple times - uses SQLAlchemy metadata.create_all.
    """
    Base.metadata.create_all(bind=engine)
    if seed:
        # Add seed data if needed (example: model registry entry)
        from sqlalchemy.orm import Session
        from models.model_registry import ModelRegistry

        db = Session(bind=engine)
        try:
            exists = db.query(ModelRegistry).filter(ModelRegistry.name == "ckd_ci_model").first()
            if not exists:
                m = ModelRegistry(name="ckd_ci_model", version="v1", description="Initial model", is_active=True)
                db.add(m)
                db.commit()
        finally:
            db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Initialize the database and optionally seed data")
    parser.add_argument("--seed", action="store_true", help="Add seed data")
    args = parser.parse_args()
    init_db(seed=args.seed)
    print("Database initialized")
