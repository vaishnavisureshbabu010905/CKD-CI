from core.metrics import get_metrics
from monitoring.drift import compute_drift_score


DRIFT_THRESHOLD = 0.25
ERROR_RATE_THRESHOLD = 0.1
LATENCY_THRESHOLD_MS = 500


def check_alerts(baseline, current, error_rate: float, avg_latency_ms: float) -> dict:
    alerts = []
    drift = compute_drift_score(baseline, current)
    if drift.get("drift_score", 0.0) > DRIFT_THRESHOLD:
        alerts.append({"type": "drift", "score": drift.get("drift_score")})
    if error_rate > ERROR_RATE_THRESHOLD:
        alerts.append({"type": "error_rate", "rate": error_rate})
    if avg_latency_ms > LATENCY_THRESHOLD_MS:
        alerts.append({"type": "latency", "latency_ms": avg_latency_ms})
    return {"alerts": alerts}
