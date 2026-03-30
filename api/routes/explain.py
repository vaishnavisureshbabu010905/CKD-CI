from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.session import get_db
from core.deps import get_current_user
from models.prediction import Prediction
from services.model_loader import get_model

router = APIRouter(prefix="/prediction", tags=["explain"])


@router.get("/explain/{prediction_id}")
def explain_prediction(prediction_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    p = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="prediction not found")

    features = p.input_features or {}
    model = get_model()
    try:
        import shap

        explainer = None
        try:
            explainer = shap.Explainer(model.model)
        except Exception:
            try:
                explainer = shap.TreeExplainer(model.model)
            except Exception:
                explainer = None

        if explainer is not None:
            vals = explainer([list(features.values())])
            # shap returns values per feature; map back to names
            feature_names = getattr(model, "feature_columns", list(features.keys()))
            shap_vals = vals.values[0].tolist() if hasattr(vals, "values") else []
            top = []
            for name, val in zip(feature_names, shap_vals):
                top.append({"feature": name, "shap_value": float(val)})
            return {"prediction_id": prediction_id, "explanation": top, "confidence": p.confidence}
    except Exception:
        # fallback: return simple feature importance if available
        fi = getattr(model, "feature_importances_", None) or getattr(getattr(model, "model", {}), "feature_importances_", None)
        if fi is not None:
            feature_names = getattr(model, "feature_columns", list(features.keys()))
            top = []
            for name, val in zip(feature_names, list(fi)):
                top.append({"feature": name, "importance": float(val)})
            return {"prediction_id": prediction_id, "explanation": top, "confidence": p.confidence}

    # If no explanation available
    return {"prediction_id": prediction_id, "explanation": None, "confidence": p.confidence}
