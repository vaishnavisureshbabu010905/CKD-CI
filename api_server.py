"""
CKD-CI FastAPI inference service.

Run:
  .venv312\\Scripts\\python.exe -m uvicorn api_server:app --reload --port 8000
"""

from __future__ import annotations

import os
from typing import Literal

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json

from db.session import SessionLocal
from models.model_registry import ModelRegistry
from fastapi import Depends
from core.deps import require_admin
from api.routes.auth import router as auth_router
from api.routes.predictions import router as predictions_router
from api.routes.admin import router as admin_router

FEATURE_COLUMNS = [
    "age",
    "education_years",
    "gender",
    "eGFR",
    "creatinine",
    "bun",
    "uacr",
    "hemoglobin",
    "albumin",
    "hsCRP",
    "potassium",
    "phosphate",
    "calcium",
    "systolic_bp",
    "bmi",
    "diabetes",
    "hypertension",
    "cvd",
]

RISK_LABELS = {
    0: "No Cognitive Risk",
    1: "Low Cognitive Risk",
    2: "Moderate Cognitive Risk",
    3: "High Cognitive Risk",
}

app = FastAPI(title="CKD-CI API", version="1.0.0")

# include auth and predictions routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(predictions_router, prefix="/predictions")
app.include_router(admin_router)

bundle_path = os.path.join("results", "model_bundle.pkl")

# Lazy-load model artifacts to avoid import-time dependency on joblib during tests
model = None
scaler = None
risk_labels = RISK_LABELS
thresholds = {}

def _load_artifacts() -> None:
    global model, scaler, risk_labels, thresholds
    try:
        import joblib
    except Exception:
        # joblib not available in minimal test environments
        model = None
        scaler = None
        return

    if os.path.exists(bundle_path):
        bundle = joblib.load(bundle_path)
        model = bundle.get("model")
        scaler = bundle.get("scaler")
        risk_labels = bundle.get("risk_labels", RISK_LABELS)
        thresholds = bundle.get("thresholds", {})
    else:
        model_path = os.path.join("results", "best_model.pkl")
        scaler_path = os.path.join("results", "scaler.pkl")
        if os.path.exists(model_path) and os.path.exists(scaler_path):
            model = joblib.load(model_path)
            scaler = joblib.load(scaler_path)
            risk_labels = RISK_LABELS
            thresholds = {}
        else:
            model = None
            scaler = None

# attempt load once
_load_artifacts()


class PatientRecord(BaseModel):
    age: float = Field(ge=20, le=95)
    education_years: float = Field(ge=0, le=25)
    gender: Literal[0, 1]
    eGFR: float = Field(ge=0, le=150)
    creatinine: float = Field(ge=0.2, le=10)
    bun: float = Field(ge=2, le=150)
    uacr: float = Field(ge=0, le=5000)
    hemoglobin: float = Field(ge=5, le=20)
    albumin: float = Field(ge=1.5, le=6)
    hsCRP: float = Field(ge=0, le=100)
    potassium: float = Field(ge=2, le=8)
    phosphate: float = Field(ge=1, le=10)
    calcium: float = Field(ge=6, le=13)
    systolic_bp: float = Field(ge=70, le=260)
    bmi: float = Field(ge=10, le=60)
    diabetes: Literal[0, 1]
    hypertension: Literal[0, 1]
    cvd: Literal[0, 1]


class BatchRequest(BaseModel):
    records: list[PatientRecord]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    from core.metrics import get_metrics

    return get_metrics()


@app.post("/predict")
def predict_one(record: PatientRecord):
    if model is None or scaler is None:
        raise HTTPException(status_code=503, detail="model artifacts not available")

    try:
        df = pd.DataFrame([record.model_dump()], columns=FEATURE_COLUMNS)
        x_scaled = scaler.transform(df)
        pred = int(model.predict(x_scaled)[0])
        proba = model.predict_proba(x_scaled)[0]

        class1_thr = thresholds.get("class_1")
        if class1_thr is not None and float(proba[1]) >= float(class1_thr):
            pred = 1

        return {
            "predicted_class": pred,
            "predicted_label": risk_labels[int(pred)],
            "probabilities": {f"class_{i}": float(p) for i, p in enumerate(proba)},
            "confidence": float(np.max(proba)),
        }
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))


@app.post("/predict-batch")
def predict_batch(request: BatchRequest):
    try:
        if not request.records:
            raise HTTPException(status_code=400, detail="records cannot be empty")

        if model is None or scaler is None:
            raise HTTPException(status_code=503, detail="model artifacts not available")

        df = pd.DataFrame([r.model_dump() for r in request.records], columns=FEATURE_COLUMNS)
        x_scaled = scaler.transform(df)
        pred = model.predict(x_scaled)
        proba = model.predict_proba(x_scaled)

        class1_thr = thresholds.get("class_1")
        if class1_thr is not None:
            pred = np.array(pred)
            pred[proba[:, 1] >= float(class1_thr)] = 1

        rows = []
        for i in range(len(df)):
            rows.append(
                {
                    "row_index": i,
                    "predicted_class": int(pred[i]),
                    "predicted_label": risk_labels[int(pred[i])],
                    "confidence": float(np.max(proba[i])),
                    "probabilities": {f"class_{k}": float(p) for k, p in enumerate(proba[i])},
                }
            )

        return {"count": len(rows), "predictions": rows}
    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))


# --- Model registry endpoints (simple CRUD) ---


class ModelIn(BaseModel):
    name: str
    version: str
    description: Optional[str] = None
    artifact_path: Optional[str] = None
    meta: Optional[dict] = None


@app.get("/models")
def list_models(current_user=Depends(require_admin)):
    db = SessionLocal()
    try:
        items = db.query(ModelRegistry).order_by(ModelRegistry.created_at.desc()).all()
        return [
            {
                "id": m.id,
                "name": m.name,
                "version": m.version,
                "description": m.description,
                "artifact_path": m.artifact_path,
                "meta": m.meta,
                "is_active": bool(m.is_active),
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in items
        ]
    finally:
        db.close()


@app.post("/models")
def register_model(payload: ModelIn, current_user=Depends(require_admin)):
    db = SessionLocal()
    try:
        m = ModelRegistry(
            name=payload.name,
            version=payload.version,
            description=payload.description,
            artifact_path=payload.artifact_path,
            meta=payload.meta or {},
            is_active=False,
        )
        db.add(m)
        db.commit()
        db.refresh(m)
        return {"id": m.id}
    except Exception as ex:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(ex))
    finally:
        db.close()


@app.post("/models/{model_id}/activate")
def activate_model(model_id: int, current_user=Depends(require_admin)):
    db = SessionLocal()
    try:
        # deactivate others
        db.query(ModelRegistry).update({ModelRegistry.is_active: False})
        m = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).one_or_none()
        if m is None:
            raise HTTPException(status_code=404, detail="model not found")
        m.is_active = True
        db.add(m)
        db.commit()
        return {"id": m.id, "is_active": True}
    except HTTPException:
        raise
    except Exception as ex:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(ex))
    finally:
        db.close()

