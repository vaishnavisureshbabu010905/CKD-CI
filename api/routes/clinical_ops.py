from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from core.deps import get_current_user
from core.metrics import get_metrics
from db.session import get_db
from ml.reproducibility import build_inference_metadata
from ml.retraining_hooks import get_retraining_hooks
from models.model_registry import ModelRegistry
from models.patient import Patient
from models.prediction import Prediction
from monitoring.alert_engine import generate_alerts
from monitoring.clinical_analytics import (
    build_feature_drift_table,
    compute_command_center,
    compute_confidence_drift,
    compute_prediction_distribution_shift,
    overall_model_health,
)
from services.synthetic_patient_generator import generate_profile

router = APIRouter(prefix="/clinical", tags=["clinical-ops"])


def _require_roles(current_user, allowed: set[str]) -> None:
    role = str(getattr(current_user, "role", "") or "").strip().lower()
    if role == "lab_technician":
        role = "nurse"
    if role not in allowed and role != "admin":
        raise HTTPException(status_code=403, detail="Insufficient privileges")


def _prediction_to_dict(p: Prediction) -> Dict[str, Any]:
    return {
        "id": p.id,
        "patient_id": p.patient_id,
        "model_name": p.model_name,
        "model_version": p.model_version,
        "predicted_label": p.predicted_label,
        "confidence": p.confidence,
        "probabilities": p.probabilities,
        "input_features": p.input_features,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "user": getattr(getattr(p, "user", None), "email", None),
    }


def _active_model(db: Session) -> ModelRegistry | None:
    return (
        db.query(ModelRegistry)
        .filter(ModelRegistry.is_active == True)
        .order_by(ModelRegistry.created_at.desc())
        .first()
    )


@router.get("/command-center")
def command_center(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_roles(current_user, {"doctor", "nurse", "ml_engineer"})
    preds = db.query(Prediction).order_by(Prediction.created_at.desc()).limit(500).all()
    active = _active_model(db)

    active_payload = {
        "name": active.model_name if active else None,
        "version": active.version if active else None,
        "metrics": (active.metrics_json if active else {}) or {},
        "created_at": active.created_at.isoformat() if (active and active.created_at) else None,
    }

    pred_rows = [_prediction_to_dict(p) for p in preds]
    kpis = compute_command_center(pred_rows, active_payload)

    return {
        "kpis": kpis,
        "active_model": active_payload,
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/monitoring")
def monitoring_summary(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_roles(current_user, {"doctor", "nurse", "ml_engineer"})
    preds = db.query(Prediction).order_by(Prediction.created_at.asc()).limit(800).all()
    rows = [_prediction_to_dict(p) for p in preds]

    conf = compute_confidence_drift(rows)
    dist = compute_prediction_distribution_shift(rows)

    metrics = get_metrics()
    pred_total = metrics.get("predictions_total", 0) or 1
    err_rate = float(metrics.get("errors", 0)) / float(pred_total)
    health = overall_model_health(conf.get("status", "Healthy"), dist.get("status", "Healthy"), error_rate=err_rate)

    latest = rows[-1] if rows else {}
    previous = rows[-2] if len(rows) > 1 else {}

    return {
        "model_health": health,
        "confidence_drift": conf,
        "prediction_distribution_drift": dist,
        "metrics": metrics,
        "alerts": generate_alerts(latest, previous, {"confidence_drift": conf}),
    }


@router.get("/drift")
def drift_panel(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_roles(current_user, {"doctor", "nurse", "ml_engineer"})
    preds = db.query(Prediction).order_by(Prediction.created_at.desc()).limit(400).all()
    rows = [_prediction_to_dict(p) for p in preds]

    active = _active_model(db)
    baseline_means = {}
    if active and isinstance(active.metrics_json, dict):
        baseline_means = active.metrics_json.get("training_feature_means") or {}

    if not baseline_means and rows:
        oldest = list(reversed(rows))[:120]
        features = [r.get("input_features") or {} for r in oldest]
        keys = {k for f in features for k in f.keys()}
        for k in keys:
            vals = []
            for f in features:
                v = f.get(k)
                try:
                    vals.append(float(v))
                except Exception:
                    continue
            baseline_means[k] = (sum(vals) / len(vals)) if vals else 0.0

    table = build_feature_drift_table(baseline_means, rows)
    flagged = [r for r in table if r.get("drift_flag")]

    return {
        "feature_drift_table": table,
        "flagged_features": flagged,
        "flagged_count": len(flagged),
    }


@router.get("/governance")
def governance_panel(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_roles(current_user, {"ml_engineer"})
    rows = db.query(ModelRegistry).order_by(ModelRegistry.created_at.desc()).all()

    registry = []
    for r in rows:
        metrics = r.metrics_json if isinstance(r.metrics_json, dict) else {}
        registry.append(
            {
                "id": r.id,
                "model_name": r.model_name,
                "version": r.version,
                "accuracy": metrics.get("accuracy"),
                "precision": metrics.get("precision"),
                "recall": metrics.get("recall"),
                "f1": metrics.get("f1"),
                "training_date": metrics.get("training_date") or (r.created_at.isoformat() if r.created_at else None),
                "status": "active" if r.is_active else (metrics.get("stage") or "inactive"),
                "metrics": metrics,
            }
        )

    return {
        "registry": registry,
        "active_model_id": next((r.id for r in rows if r.is_active), None),
    }


@router.post("/governance/activate/{model_id}")
def activate_model(model_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_roles(current_user, {"ml_engineer"})
    m = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Model not found")

    db.query(ModelRegistry).filter(ModelRegistry.is_active == True).update({"is_active": False})
    m.is_active = True
    db.add(m)
    db.commit()
    return {"status": "activated", "model_id": model_id}


@router.post("/governance/deactivate/{model_id}")
def deactivate_model(model_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_roles(current_user, {"ml_engineer"})
    m = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Model not found")
    m.is_active = False
    db.add(m)
    db.commit()
    return {"status": "deactivated", "model_id": model_id}


@router.get("/prediction-logs")
def prediction_logs(limit: int = 200, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_roles(current_user, {"doctor", "nurse", "ml_engineer"})
    rows = db.query(Prediction).order_by(Prediction.created_at.desc()).limit(limit).all()
    return [_prediction_to_dict(p) for p in rows]


@router.get("/patient/{patient_id}/longitudinal")
def patient_longitudinal(patient_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_roles(current_user, {"doctor", "nurse"})
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    preds = (
        db.query(Prediction)
        .filter(Prediction.patient_id == patient_id)
        .order_by(Prediction.created_at.asc())
        .all()
    )

    timeline = []
    prev_rank = None
    escalations = []
    rank_map = {"0": 0, "1": 1, "2": 2, "3": 3}

    for p in preds:
        label = str(p.predicted_label)
        rank = rank_map.get(label, 0)
        features = p.input_features or {}
        row = {
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "predicted_label": p.predicted_label,
            "confidence": p.confidence,
            "egfr": features.get("egfr"),
            "creatinine": features.get("creatinine"),
            "risk_rank": rank,
            "model_version": p.model_version,
        }
        timeline.append(row)

        if prev_rank is not None and rank > prev_rank:
            escalations.append(
                {
                    "from": prev_rank,
                    "to": rank,
                    "at": row["created_at"],
                    "severity": "WARNING" if rank < 3 else "CRITICAL",
                }
            )
        prev_rank = rank

    return {
        "patient": {
            "id": patient.id,
            "patient_identifier": patient.patient_identifier,
            "features": patient.features,
        },
        "timeline": timeline,
        "risk_escalations": escalations,
    }


@router.get("/performance")
def performance_snapshot(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_roles(current_user, {"ml_engineer", "doctor"})
    active = _active_model(db)
    metrics = (active.metrics_json if (active and isinstance(active.metrics_json, dict)) else {})
    return {
        "accuracy": metrics.get("accuracy"),
        "precision": metrics.get("precision"),
        "recall": metrics.get("recall"),
        "f1": metrics.get("f1"),
        "model_version": active.version if active else None,
    }


@router.get("/system-health")
def system_health(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_roles(current_user, {"doctor", "nurse", "ml_engineer"})

    db_status = "up"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "down"

    active = _active_model(db)
    model_status = "up" if active else "warning"

    return {
        "api_status": "up",
        "db_status": db_status,
        "model_status": model_status,
        "active_model_version": active.version if active else None,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/future-hooks")
def future_hooks(current_user=Depends(get_current_user)):
    _require_roles(current_user, {"ml_engineer"})
    return get_retraining_hooks()


@router.get("/synthetic/{profile}")
def synthetic_profile(profile: str, current_user=Depends(get_current_user)):
    _require_roles(current_user, {"doctor", "nurse", "ml_engineer"})
    return {"profile": profile, "features": generate_profile(profile)}


@router.post("/inference-metadata")
def inference_metadata(payload: Dict[str, Any], current_user=Depends(get_current_user)):
    _require_roles(current_user, {"doctor", "nurse", "ml_engineer"})
    return build_inference_metadata(
        features=payload.get("features") or {},
        model_version=str(payload.get("model_version") or "unknown"),
        user_email=getattr(current_user, "email", None),
    )
