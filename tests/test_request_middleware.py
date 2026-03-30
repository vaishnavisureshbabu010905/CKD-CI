from fastapi.testclient import TestClient
from main import app
import services.model_loader as ml
import types


class DummyModel:
    def __init__(self):
        self.classes_ = [0]

    def predict_proba(self, X):
        import numpy as np

        return np.array([[1.0]])


class DummyBundle:
    def __init__(self):
        self.model = DummyModel()
        self.feature_columns = []
        self._version = "v1"
        self.metadata = {"name": "ckd_ci_model"}

    def predict_proba(self, X):
        return self.model.predict_proba(X)

    @property
    def version(self):
        return self._version


def test_request_id_header_and_prediction_time(monkeypatch):
    client = TestClient(app)

    # Override get_model to prevent loading bundle
    monkeypatch.setattr(ml, "get_model", lambda: DummyBundle())

    # Override auth dependency to bypass JWT
    from core.deps import get_current_user

    def fake_user():
        return types.SimpleNamespace(id=1, role="doctor")

    app.dependency_overrides[get_current_user] = fake_user

    # Override db dependency to a lightweight fake
    from db.session import get_db

    def fake_db():
        class FakeDB:
            def query(self, *args, **kwargs):
                return []

            def add(self, obj):
                pass

            def commit(self):
                pass

            def refresh(self, obj):
                try:
                    obj.id = 1
                except Exception:
                    pass

        yield FakeDB()

    app.dependency_overrides[get_db] = fake_db

    payload = {"patient_identifier": "p1", "features": {"age": 60}}
    r = client.post("/predictions/predict", json=payload)
    assert r.status_code == 200
    assert "X-Request-ID" in r.headers
    # cleanup overrides
    app.dependency_overrides.clear()
