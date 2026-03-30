from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
import logging

from core.deps import get_current_user
from db.session import get_db
from models.model_registry import ModelRegistry

router = APIRouter(prefix="/models", tags=["models"])
logger = logging.getLogger(__name__)


def _stage_for(row: ModelRegistry) -> str:
    if isinstance(row.meta, dict) and row.meta.get("stage"):
        return str(row.meta.get("stage"))
    return "prod" if bool(row.is_active) else "dev"


@router.get("/")
def list_models(db: Session = Depends(get_db)):
    try:
        rows = db.query(ModelRegistry).order_by(ModelRegistry.created_at.desc()).all()
        return [
            {
                "id": r.id,
                "model_name": r.model_name,
                "version": r.version,
                "stage": _stage_for(r),
                "metrics": r.metrics_json or r.meta or {},
                "artifact_path": r.artifact_path,
                "is_active": bool(r.is_active),
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    except Exception as exc:
        logger.exception("Error in list_models")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/active")
def active_model(db: Session = Depends(get_db)):
    try:
        active = (
            db.query(ModelRegistry)
            .filter(ModelRegistry.is_active == True)
            .order_by(ModelRegistry.created_at.desc())
            .first()
        )
        if not active:
            raise HTTPException(status_code=404, detail="No active model found")
        return {
            "model_id": active.id,
            "model_name": active.model_name,
            "version": active.version,
            "metrics": active.metrics_json or active.meta or {},
            "stage": _stage_for(active),
            "is_active": bool(active.is_active),
            "created_at": active.created_at.isoformat() if active.created_at else None,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error in active_model")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/register")
def register_model_entry(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="admin role required")
    try:
        model_name = payload.get("model_name") or payload.get("name")
        version = payload.get("version")
        artifact_path = payload.get("artifact_path") or payload.get("artifact")
        stage = payload.get("stage") or payload.get("target_stage") or "dev"
        metrics = payload.get("metrics") or payload.get("metrics_json") or payload.get("meta") or {}

        if not model_name or not version:
            raise HTTPException(status_code=400, detail="model_name/name and version are required")

        entry = ModelRegistry(
            model_name=model_name,
            version=version,
            metrics_json=metrics or {},
            artifact_path=artifact_path,
        )
        if isinstance(entry.meta, dict):
            entry.meta = {**entry.meta, "stage": stage or "dev"}
        else:
            entry.meta = {"stage": stage or "dev"}
        if stage == "prod":
            db.query(ModelRegistry).filter(ModelRegistry.is_active == True).update({"is_active": False})
            entry.is_active = True

        db.add(entry)
        db.commit()
        db.refresh(entry)
        return {"id": entry.id, "status": "registered"}
    except Exception as exc:
        db.rollback()
        logger.exception("Error registering model entry")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/promote")
def promote_model(model_id: int, target_stage: str = "staging", db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="admin role required")
    try:
        m = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
        if not m:
            raise HTTPException(status_code=404, detail="model not found")
        meta = m.meta if isinstance(m.meta, dict) else {}
        meta["stage"] = target_stage
        m.meta = meta
        if target_stage == "prod":
            db.query(ModelRegistry).filter(ModelRegistry.is_active == True).update({"is_active": False})
            m.is_active = True
        else:
            m.is_active = False
        db.add(m)
        db.commit()
        return {"status": "promoted", "model_id": m.id, "stage": _stage_for(m)}
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("Error promoting model")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/deprecate")
def deprecate_model(model_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="admin role required")
    try:
        m = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
        if not m:
            raise HTTPException(status_code=404, detail="model not found")
        meta = m.meta if isinstance(m.meta, dict) else {}
        meta["stage"] = "deprecated"
        m.meta = meta
        m.is_active = False
        db.add(m)
        db.commit()
        return {"status": "deprecated", "model_id": m.id}
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("Error deprecating model")
        raise HTTPException(status_code=500, detail=str(exc))
