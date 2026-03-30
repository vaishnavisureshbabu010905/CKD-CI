from fastapi import APIRouter, Response
from monitoring.drift import compute_drift_score
from monitoring.metrics_collector import metrics_text
from core.metrics import get_metrics
from core.cache import list_predictions

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/drift")
def drift():
    # For demo, compute drift for 'egfr' using last cached predictions vs baseline sample
    cached = list_predictions()
    if not cached or len(cached) < 10:
        return {"drift_score": 0.0, "drift_detected": False, "note": "insufficient data"}

    # extract egfr from cached entries if present in input_features (best-effort)
    baseline = []
    current = []
    for i, p in enumerate(reversed(cached)):
        features = p.get("input_features") or {}
        if features and "egfr" in features:
            if i < len(cached) // 2:
                baseline.append(float(features.get("egfr") or 0))
            else:
                current.append(float(features.get("egfr") or 0))

    if not baseline or not current:
        return {"drift_score": 0.0, "drift_detected": False, "note": "no egfr data"}

    return compute_drift_score(baseline, current)


@router.get("/metrics")
def prometheus_metrics():
    # expose prometheus metrics raw text
    data = metrics_text()
    return Response(content=data, media_type="text/plain; version=0.0.4")


@router.get("/summary")
def summary():
    return get_metrics()
