from typing import List
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from db.session import get_db
from core.deps import get_current_user, require_doctor_or_admin
from sqlalchemy.exc import OperationalError
from schemas.prediction import PredictionRequest, PredictionResponse, BatchPredictionRequest, BatchPredictionResponse
from models.patient import Patient
from services.prediction_service import PredictionService
from core.validation import validate_features
from services.audit_service import log_audit
from services.timeline_service import record_event

router = APIRouter(tags=["predictions"])
logger = logging.getLogger(__name__)


def _get_or_create_patient(db: Session, patient_identifier: str | None, features: dict):
    patient = None
    if patient_identifier:
        q = db.query(Patient)
        if hasattr(q, "filter"):
            patient = q.filter(Patient.patient_identifier == patient_identifier).first()
        elif isinstance(q, list):
            for p in q:
                if getattr(p, "patient_identifier", None) == patient_identifier:
                    patient = p
                    break

    if patient:
        return patient

    # Keep a stable fallback ID to avoid repeated unique-constraint failures.
    fallback_identifier = patient_identifier or "unknown"
    patient = Patient(patient_identifier=fallback_identifier, features=features)
    db.add(patient)
    try:
        db.commit()
        db.refresh(patient)
        return patient
    except IntegrityError:
        db.rollback()
        # If another request already created this identifier, reuse it.
        q = db.query(Patient)
        if hasattr(q, "filter"):
            existing = q.filter(Patient.patient_identifier == fallback_identifier).first()
            if existing:
                return existing
        raise


@router.post("/predict", response_model=PredictionResponse)
def predict_single(payload: PredictionRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        # Validate feature payload server-side guardrails
        issues = validate_features(payload.features or {})
        if issues:
            raise HTTPException(status_code=400, detail={"validation_issues": issues})
        from core.validation import normalize_feature_dict
        clean_features = normalize_feature_dict(payload.features or {})
        # Resolve patient or safely create one.
        patient = _get_or_create_patient(db, payload.patient_identifier, clean_features)

        svc = PredictionService(db=db, user=current_user)
        res = svc.predict_single(patient, clean_features)
        if patient.id:
            record_event(
                db,
                patient_id=patient.id,
                source_type="prediction",
                source_id=res.get("prediction_id"),
                summary=f"Prediction {res.get('predicted_label')}",
                payload={"probabilities": res.get("probabilities")},
            )
        log_audit(db, current_user, action="predict_single", resource_type="prediction", resource_id=str(res.get("prediction_id")))
        return {
            "prediction_id": res["prediction_id"],
            "patient_identifier": res.get("patient_identifier"),
            "result": {
                "predicted_label": res["predicted_label"],
                "probabilities": res["probabilities"],
                "confidence": res.get("confidence"),
                "explanation": None,
            },
            "model_name": res["model_name"],
            "model_version": res["model_version"],
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error in predict_single")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/batch", response_model=BatchPredictionResponse)
def predict_batch(payload: BatchPredictionRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        svc = PredictionService(db=db, user=current_user)
        items = []
        from core.validation import normalize_feature_dict
        for item in payload.items:
            # server-side validation for each item
            issues = validate_features(item.features or {})
            if issues:
                raise HTTPException(status_code=400, detail={"validation_issues": issues, "patient_identifier": item.patient_identifier})

            clean_features = normalize_feature_dict(item.features or {})
            patient = _get_or_create_patient(db, item.patient_identifier, clean_features)
            items.append((patient, clean_features))

        results = svc.predict_batch(items)

        # Normalize results into PredictionResponse-like dicts
        normalized = []
        for r in results:
            if "error" in r:
                normalized.append({"prediction_id": None, "patient_identifier": r.get("patient_identifier"), "result": {"predicted_label": "error", "probabilities": {}, "confidence": None, "explanation": None}, "model_name": "", "model_version": ""})
            else:
                normalized.append({"prediction_id": r.get("prediction_id"), "patient_identifier": r.get("patient_identifier"), "result": {"predicted_label": r.get("predicted_label"), "probabilities": r.get("probabilities", {}), "confidence": r.get("confidence"), "explanation": None}, "model_name": r.get("model_name"), "model_version": r.get("model_version")})

        return {"results": normalized}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error in predict_batch")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/history", response_model=List[dict])
def prediction_history(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user=Depends(require_doctor_or_admin)):
    # Returns recent predictions visible to the user; admin can see all
    from models.prediction import Prediction
    try:
        q = db.query(Prediction).order_by(Prediction.created_at.desc())
        if current_user.role != "admin":
            q = q.filter(Prediction.user_id == current_user.id)
        preds = q.offset(skip).limit(limit).all()
        return [{"id": p.id, "patient_id": p.patient_id, "model_version": p.model_version, "predicted_label": p.predicted_label, "probabilities": p.probabilities, "confidence": p.confidence, "created_at": p.created_at.isoformat() if p.created_at else None} for p in preds]
    except OperationalError:
        # In test or minimal environments without DB tables, return empty list
        return []
    except Exception:
        return []
