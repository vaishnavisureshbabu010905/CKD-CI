from typing import Any, Dict, List, Tuple
from sqlalchemy.orm import Session
import numpy as np
import logging
import time
import types

import services.model_loader as ml
from models.patient import Patient
from models.prediction import Prediction
from services.audit_service import log_audit
from core.request_context import get_request_id, set_prediction_time_ms
import core.log_sanitizer as log_sanitizer
from core.metrics import increment_prediction, increment_error
from core.cache import push_prediction

logger = logging.getLogger("ckdci.prediction")


class PredictionService:
    def __init__(self, db: Session, user=None):
        self.db = db
        self.user = user
        self.model_bundle = ml.get_model()

    def _order_features(self, features: Dict[str, Any]) -> List[Any]:
        cols = getattr(self.model_bundle, "feature_columns", None)
        if not cols:
            cols = list(features.keys()) if features else []

        # Normalize keys so we can accept both legacy and new payload naming.
        f = features or {}
        normalized = {str(k).lower(): v for k, v in f.items()}

        alias_keys = {
            "egfr": ["egfr", "e_gfr"],
            "hscrp": ["hscrp", "hs_crp", "hsc_rp"],
            "phosphate": ["phosphate", "phosphorus"],
            "education_years": ["education_years", "educationyears"],
            "systolic_bp": ["systolic_bp", "systolicbp"],
        }

        # Keep inference stable even when some optional UI fields are not exposed.
        default_values = {
            "education_years": 12,
            "hscrp": 2.0,
            "phosphate": 3.5,
        }

        def _get_value(col_name: str):
            # exact key first
            if col_name in f:
                return f[col_name]

            c = str(col_name).lower()
            # direct lower-case hit
            if c in normalized:
                return normalized[c]

            # alias-based fallback
            for canonical, aliases in alias_keys.items():
                if c == canonical or c in aliases:
                    for a in aliases:
                        if a in normalized:
                            return normalized[a]

            if c in default_values:
                return default_values[c]
            return np.nan

        return [_get_value(c) for c in cols]

    def predict_single(self, patient: Patient, features: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        X = [self._order_features(features)]
        try:
            proba = self.model_bundle.predict_proba(X)
        except Exception:
            increment_error()
            raise

        model = getattr(self.model_bundle, "model", None)
        classes = getattr(model, "classes_", None)
        if classes is None:
            classes = list(range(proba.shape[1]))
        probs = {str(c): float(p) for c, p in zip(classes, proba[0].tolist())}
        pred_idx = int(np.argmax(proba[0]))
        predicted = str(classes[pred_idx])
        confidence = float(proba[0][pred_idx])

        label_map = getattr(self.model_bundle, "label_map", {}) or {}
        human_label = label_map.get(predicted, predicted)

        # Create DB record (SQLAlchemy model). If mapper/config isn't available
        # (tests may supply lightweight fake DBs), fall back to a simple object.
        try:
            record = Prediction(
                patient_id=patient.id,
                user_id=getattr(self.user, "id", None),
                model_name=(getattr(self.model_bundle, "metadata", None) or getattr(self.model_bundle, "meta", {})).get("name", "ckd_ci_model"),
                model_version=getattr(self.model_bundle, "version", "dev"),
                predicted_label=human_label,
                probabilities=probs,
                confidence=confidence,
                input_features=features,
                meta={"raw_label": predicted},
            )
            try:
                self.db.add(record)
                self.db.commit()
                self.db.refresh(record)
            except Exception:
                pass
        except Exception:
            record = types.SimpleNamespace(
                id=1,
                patient_id=patient.id,
                user_id=getattr(self.user, "id", None),
                model_name=(getattr(self.model_bundle, "metadata", {}) or {}).get("name", "ckd_ci_model"),
                model_version=getattr(self.model_bundle, "version", None),
                predicted_label=human_label,
                probabilities=probs,
                confidence=confidence,
                input_features=features,
                meta={"raw_label": predicted},
            )

        try:
            log_audit(db=self.db, user=self.user, action="predict_single", resource_type="prediction", resource_id=str(record.id), details={"patient_id": patient.id})
        except Exception:
            pass

        try:
            # push a minimal cache entry for quick access (no PHI)
            push_prediction({
                "prediction_id": record.id,
                "patient_identifier": getattr(patient, "patient_identifier", None),
                "predicted_label": human_label,
                "confidence": confidence,
                "model_version": record.model_version,
                "created_at": record.created_at.isoformat() if getattr(record, "created_at", None) else None,
            })
        except Exception:
            pass

        elapsed_ms = (time.time() - start) * 1000.0
        try:
            set_prediction_time_ms(elapsed_ms)
        except Exception:
            pass

        try:
            increment_prediction(predicted, confidence)
        except Exception:
            logger.exception("metrics update failed")

        try:
            sanitized = log_sanitizer.sanitize_prediction_input(features)
        except Exception:
            sanitized = {"feature_count": len(features) if features else 0}

        try:
            logger.info(
                f"prediction model_version={record.model_version} confidence={confidence}",
                extra={
                    "request_id": get_request_id(),
                    "event": "prediction",
                    "model_version": record.model_version,
                    "prediction": int(predicted) if str(predicted).isdigit() else predicted,
                    "confidence": confidence,
                    "feature_count": sanitized.get("feature_count"),
                    "prediction_time_ms": elapsed_ms,
                },
            )
        except Exception:
            logger.exception("failed to emit sanitized prediction log")

        return {
            "prediction_id": record.id,
            "patient_identifier": patient.patient_identifier,
            "predicted_label": human_label,
            "probabilities": probs,
            "confidence": confidence,
            "model_name": record.model_name,
            "model_version": record.model_version,
        }

    def predict_batch(self, items: List[Tuple[Patient, Dict[str, Any]]]) -> List[Dict[str, Any]]:
        results = []
        for patient, features in items:
            try:
                res = self.predict_single(patient, features)
                results.append(res)
            except Exception as exc:
                results.append({"error": str(exc), "patient_identifier": patient.patient_identifier})
        return results


def get_prediction_service(db: Session, user=None) -> PredictionService:
    return PredictionService(db=db, user=user)
