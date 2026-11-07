import types
from fastapi.testclient import TestClient

from main import app
from core.deps import get_current_user
from db.session import get_db

client = TestClient(app)


def fake_user(role):
    def _user():
        return types.SimpleNamespace(id=1, role=role, email=f"{role}@example.com")

    return _user


def test_models_admin_only():
    # non-admin should be forbidden
    app.dependency_overrides[get_current_user] = fake_user("doctor")
    r = client.get("/models")
    assert r.status_code == 403

    # admin should be allowed (may return empty list)
    app.dependency_overrides[get_current_user] = fake_user("admin")
    # prevent DB mapper initialization by providing a fake SessionLocal that returns
    # a lightweight object with a query() method
    class FakeDB:
        def __init__(self):
            self._models = []
            self._preds = []

        def add(self, obj):
            if not hasattr(obj, "id") or getattr(obj, "id") is None:
                obj.id = 1
            self._models.append(obj)

        def commit(self):
            return None

        def refresh(self, obj):
            if not hasattr(obj, "id") or getattr(obj, "id") is None:
                obj.id = len(self._models) or 1

        def rollback(self):
            return None

        def close(self):
            return None

        def query(self, model):
            class Q:
                def __init__(self):
                    self._data = []

                def order_by(self, *a, **k):
                    return self

                def all(self):
                    return []

                def limit(self, n):
                    return self

                def offset(self, s):
                    return self

                def filter(self, *args, **kwargs):
                    return self

                def one_or_none(self):
                    return None

                def first(self):
                    return None

                def update(self, *args, **kwargs):
                    return True

            return Q()

    app.dependency_overrides[get_db] = lambda: FakeDB()
    r = client.get("/models")
    assert r.status_code == 200


def test_post_models_admin_only():
    app.dependency_overrides[get_current_user] = fake_user("doctor")
    r = client.post("/models", json={"name": "m", "version": "v1"})
    assert r.status_code == 403

    app.dependency_overrides[get_current_user] = fake_user("admin")
    r = client.post("/models", json={"name": "m", "version": "v1"})
    assert r.status_code in (200, 201)


def test_activate_model_non_admin_forbidden():
    app.dependency_overrides[get_current_user] = fake_user("doctor")
    r = client.post("/models/1/activate")
    assert r.status_code == 403

    app.dependency_overrides[get_current_user] = fake_user("admin")
    r = client.post("/models/1/activate")
    assert r.status_code != 403


def test_prediction_history_access():
    app.dependency_overrides[get_current_user] = fake_user("nurse")
    r = client.get("/predictions/history")
    assert r.status_code == 403

    app.dependency_overrides[get_current_user] = fake_user("doctor")
    r = client.get("/predictions/history")
    assert r.status_code == 200


def test_dashboard_mode_access_control():
    # import compute_allowed_modes from dashboard
    from dashboard import compute_allowed_modes

    assert "Admin Analytics" not in compute_allowed_modes("lab_technician")
    assert "Admin Analytics" in compute_allowed_modes("admin")
    assert "Prediction History" in compute_allowed_modes("doctor")
    assert "Prediction History" not in compute_allowed_modes("lab_technician")
