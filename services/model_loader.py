import os
from typing import Any, Dict, List, Optional

from config.settings import settings


class ModelBundle:
    """Loads and exposes the CKD-CI model bundle.

    The bundle is expected to be a joblib file containing at least:
      - 'model': a sklearn-like estimator with `predict_proba` or `predict`
      - 'feature_columns': ordered list of feature column names
      - 'label_map': optional mapping from numeric labels to human labels
      - 'version': version string
      - other metadata
    """

    def __init__(self, path: Optional[str] = None):
        env_path = os.getenv("MODEL_BUNDLE_PATH")
        default_path = os.path.join(os.path.dirname(__file__), "..", "models", "ckd_model_bundle.joblib")
        fallback_path = os.path.join(os.path.dirname(__file__), "..", "results", "model_bundle.pkl")

        candidate_paths = [p for p in [path, env_path, default_path, fallback_path] if p]
        resolved_path = candidate_paths[0]
        for candidate in candidate_paths:
            if os.path.exists(candidate):
                resolved_path = candidate
                break

        self.path = resolved_path
        self.bundle: Dict[str, Any] = {}

    def load(self) -> None:
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"Model bundle not found at {self.path}")
        # import joblib lazily to avoid hard dependency during tests
        try:
            import joblib

            self.bundle = joblib.load(self.path)
        except Exception:
            # if joblib isn't available (e.g., in lightweight test runs), leave bundle empty
            self.bundle = {}

    @property
    def model(self):
        return self.bundle.get("model")

    @property
    def feature_columns(self) -> List[str]:
        return self.bundle.get("feature_columns", [])

    @property
    def label_map(self) -> Dict[Any, str]:
        return self.bundle.get("label_map") or self.bundle.get("risk_labels") or {
            0: "No Cognitive Risk",
            1: "Low Cognitive Risk",
            2: "Moderate Cognitive Risk",
            3: "High Cognitive Risk",
            "0": "No Cognitive Risk",
            "1": "Low Cognitive Risk",
            "2": "Moderate Cognitive Risk",
            "3": "High Cognitive Risk",
        }

    @property
    def scaler(self):
        return self.bundle.get("scaler")

    @property
    def version(self) -> str:
        return self.bundle.get("version") or self.bundle.get("run_id", "prod-v1.0")

    @property
    def metadata(self) -> Dict[str, Any]:
        return self.bundle.get("metadata", {})

    def predict_proba(self, X):
        model = self.model
        scaler = self.scaler
        if scaler is not None:
            try:
                import pandas as pd
                cols = self.feature_columns
                if cols and len(cols) == (len(X[0]) if hasattr(X, "__len__") and len(X) else 0):
                    X_df = pd.DataFrame(X, columns=cols)
                    X = scaler.transform(X_df)
                else:
                    X = scaler.transform(X)
            except Exception:
                pass

        if hasattr(model, "predict_proba"):
            return model.predict_proba(X)
        # fallback: if model only has predict, return one-hot like probabilities
        preds = model.predict(X)
        # build crude probability array: 1.0 for predicted class
        import numpy as np

        classes = getattr(model, "classes_", None)
        if classes is None:
            # unknown classes: return zeros
            return np.zeros((len(preds), 1))
        proba = np.zeros((len(preds), len(classes)))
        for i, p in enumerate(preds):
            idx = list(classes).index(p)
            proba[i, idx] = 1.0
        return proba

    def predict(self, X):
        model = self.model
        return model.predict(X)

    def explain(self, X):
        # Placeholder: return empty explanation or SHAP values if available in bundle
        explainer = self.bundle.get("explainer")
        if explainer is not None:
            try:
                return explainer.shap_values(X)
            except Exception:
                return None
        return None


_global_model: Optional[ModelBundle] = None


def get_model() -> ModelBundle:
    global _global_model
    if _global_model is None:
        _global_model = ModelBundle()
        _global_model.load()
    return _global_model
