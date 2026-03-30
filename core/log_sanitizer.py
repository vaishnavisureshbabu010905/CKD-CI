"""PHI-safe log sanitizer for prediction inputs.

Provides helper `sanitize_prediction_input` which maps sensitive numeric
values to categorical buckets and ensures raw patient values are never
logged. Only non-PHI fields (counts and buckets) are returned.
"""
from typing import Dict, Any


def _bucket_egfr(val: float) -> str:
    try:
        v = float(val)
    except Exception:
        return "unknown"
    if v < 30:
        return "very_low"
    if v < 60:
        return "low"
    if v < 90:
        return "normal"
    return "high"


def _bucket_simple(val: float, low: float, high: float) -> str:
    try:
        v = float(val)
    except Exception:
        return "unknown"
    if v < low:
        return "low"
    if v > high:
        return "high"
    return "normal"


def sanitize_prediction_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """Return a PHI-safe sanitized summary of the input features.

    The sanitizer MUST NOT include raw numeric values that could be PHI.
    Instead, it returns counts and range buckets for key clinical labs.
    """
    if not isinstance(data, dict):
        return {"feature_count": 0}

    # Allowed direct fields
    allowed = ["age", "gender", "education_years", "diabetes", "hypertension", "cvd"]

    out: Dict[str, Any] = {}
    out["feature_count"] = len(data)

    for k in allowed:
        if k in data:
            out[k] = data.get(k)

    # Kidney-related
    if "egfr" in data:
        out["egfr_range"] = _bucket_egfr(data.get("egfr"))
    if "creatinine" in data:
        out["creatinine_range"] = _bucket_simple(data.get("creatinine"), low=0.6, high=1.3)
    if "bun" in data:
        out["bun_range"] = _bucket_simple(data.get("bun"), low=7, high=20)
    if "uacr" in data:
        out["uacr_range"] = _bucket_simple(data.get("uacr"), low=0, high=30)

    # Other labs
    if "hemoglobin" in data:
        out["hemoglobin_range"] = _bucket_simple(data.get("hemoglobin"), low=11, high=17)
    if "albumin" in data:
        out["albumin_range"] = _bucket_simple(data.get("albumin"), low=3.5, high=5.0)
    if "hsCRP" in data or "hs_crp" in data:
        out["hscrp_range"] = _bucket_simple(data.get("hsCRP", data.get("hs_crp")), low=0, high=3)

    # Vitals
    if "systolic_bp" in data:
        out["bp_range"] = _bucket_simple(data.get("systolic_bp"), low=90, high=140)
    if "bmi" in data:
        out["bmi_range"] = _bucket_simple(data.get("bmi"), low=18.5, high=25)

    return out
