from fastapi.testclient import TestClient
from main import app


def test_metrics_endpoint():
    client = TestClient(app)
    r = client.get("/metrics")
    assert r.status_code == 200
    js = r.json()
    assert "predictions_total" in js
    assert "errors" in js
    assert "avg_confidence" in js
    assert "class_distribution" in js
