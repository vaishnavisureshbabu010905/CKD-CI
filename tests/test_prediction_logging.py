import json
import types
import numpy as np
import logging

from core import log_sanitizer
from services.prediction_service import PredictionService


class FakeModel:
    def __init__(self):
        self.classes_ = np.array([0, 1, 2, 3])

    def predict_proba(self, X):
        return np.array([[0.1, 0.1, 0.7, 0.1]])


class FakeBundle:
    def __init__(self):
        self.model = FakeModel()
        self.feature_columns = ["a", "b"]
        self.bundle = {}
        self._version = "v1"
        self.metadata = {"name": "ckd_ci_model"}

    def predict_proba(self, X):
        return self.model.predict_proba(X)

    @property
    def version(self):
        return self._version

    @property
    def label_map(self):
        return {}


class FakeDB:
    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        pass

    def refresh(self, obj):
        try:
            obj.id = 1
        except Exception:
            pass


def test_prediction_logging_sanitized(monkeypatch, caplog):
    caplog.set_level(logging.INFO)

    # Monkeypatch model loader to return fake bundle
    import services.model_loader as ml

    monkeypatch.setattr(ml, "get_model", lambda: FakeBundle())

    # Monkeypatch sanitize to ensure called
    called = {"sanitized": False}

    def fake_sanitize(data):
        called["sanitized"] = True
        return {"feature_count": len(data)}

    monkeypatch.setattr(log_sanitizer, "sanitize_prediction_input", fake_sanitize)

    fake_db = FakeDB()
    fake_user = types.SimpleNamespace(id=2)
    svc = PredictionService(db=fake_db, user=fake_user)

    patient = types.SimpleNamespace(id=5, patient_identifier="P1")
    features = {"creatinine": 2.3, "egfr": 40, "age": 65}

    res = svc.predict_single(patient, features)

    assert called["sanitized"] is True
    # Ensure returned prediction contains model_version and confidence
    assert "model_version" in res
    assert "confidence" in res

    # Ensure logs do not contain raw numeric value '2.3'
    assert "2.3" not in caplog.text
    # Ensure structured fields present in logs
    assert "prediction" in caplog.text
    assert "confidence" in caplog.text
    assert "model_version" in caplog.text
