from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import mean
from typing import Dict, Iterable, List


DEFAULT_FEATURES = [
    "age",
    "bmi",
    "egfr",
    "creatinine",
    "bun",
    "uacr",
    "hemoglobin",
    "albumin",
    "potassium",
    "phosphorus",
    "calcium",
    "systolic_bp",
    "diabetes",
    "hypertension",
    "cvd",
]


@dataclass
class DriftRow:
    feature: str
    training_mean: float
    current_mean: float
    drift_pct: float
    drift_flag: bool


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _mean(values: Iterable[float]) -> float:
    values = list(values)
    return mean(values) if values else 0.0


def _risk_label(raw: object) -> str:
    text = str(raw or "").strip().lower()
    if text in {"0", "no risk", "no cognitive risk"}:
        return "No Risk"
    if text in {"1", "low risk", "low cognitive risk"}:
        return "Low Risk"
    if text in {"2", "moderate risk", "moderate cognitive risk"}:
        return "Moderate Risk"
    if text in {"3", "high risk", "high cognitive risk"}:
        return "High Risk"
    return "Unknown"


def compute_command_center(predictions: List[dict], active_model: dict | None) -> Dict[str, object]:
    now = datetime.utcnow()
    today = now.date()

    total = len(predictions)
    today_rows = []
    confidences = []
    labels = []

    for p in predictions:
        created = p.get("created_at")
        created_dt = None
        if created:
            try:
                created_dt = datetime.fromisoformat(str(created).replace("Z", "+00:00")).replace(tzinfo=None)
            except Exception:
                created_dt = None
        if created_dt and created_dt.date() == today:
            today_rows.append(p)

        confidence = _safe_float(p.get("confidence"), default=-1.0)
        if confidence >= 0:
            confidences.append(confidence)

        labels.append(_risk_label(p.get("predicted_label")))

    critical_count = sum(1 for lbl in labels if lbl == "High Risk")
    label_counts = dict(Counter(labels))

    recent_24h = [
        p for p in predictions
        if p.get("created_at")
        and (now - datetime.fromisoformat(str(p.get("created_at")).replace("Z", "+00:00")).replace(tzinfo=None)) <= timedelta(hours=24)
    ] if predictions else []

    accuracy_snapshot = _safe_float((active_model or {}).get("metrics", {}).get("accuracy"), 0.0)
    avg_conf = _mean(confidences)

    return {
        "patients_processed_today": len(today_rows),
        "critical_patients": critical_count,
        "prediction_volume": total,
        "average_confidence": avg_conf,
        "model_accuracy_snapshot": accuracy_snapshot,
        "risk_distribution": label_counts,
        "recent_24h_count": len(recent_24h),
    }


def compute_confidence_drift(predictions: List[dict]) -> Dict[str, object]:
    conf = [_safe_float(p.get("confidence"), default=-1.0) for p in predictions]
    conf = [c for c in conf if c >= 0]
    if len(conf) < 20:
        return {"drift_pct": 0.0, "status": "Healthy", "note": "insufficient data"}

    half = len(conf) // 2
    baseline = _mean(conf[:half])
    current = _mean(conf[half:])
    if baseline <= 0:
        return {"drift_pct": 0.0, "status": "Healthy", "note": "baseline unavailable"}

    drift_pct = ((current - baseline) / baseline) * 100.0
    status = "Healthy"
    if drift_pct < -15:
        status = "Needs retraining"
    elif drift_pct < -8:
        status = "Warning"

    return {
        "baseline_confidence": baseline,
        "current_confidence": current,
        "drift_pct": drift_pct,
        "status": status,
    }


def compute_prediction_distribution_shift(predictions: List[dict]) -> Dict[str, object]:
    labels = [_risk_label(p.get("predicted_label")) for p in predictions]
    if len(labels) < 20:
        return {"shift_score": 0.0, "status": "Healthy", "note": "insufficient data"}

    half = len(labels) // 2
    base_counts = Counter(labels[:half])
    cur_counts = Counter(labels[half:])
    keys = sorted(set(base_counts.keys()) | set(cur_counts.keys()))

    base_total = sum(base_counts.values()) or 1
    cur_total = sum(cur_counts.values()) or 1
    shift = 0.0
    for k in keys:
        b = base_counts.get(k, 0) / base_total
        c = cur_counts.get(k, 0) / cur_total
        shift += abs(c - b)

    shift_score = shift / 2.0
    status = "Healthy"
    if shift_score > 0.3:
        status = "Needs retraining"
    elif shift_score > 0.18:
        status = "Warning"

    return {
        "shift_score": shift_score,
        "status": status,
        "baseline_distribution": dict(base_counts),
        "current_distribution": dict(cur_counts),
    }


def build_feature_drift_table(
    baseline_means: Dict[str, float],
    predictions: List[dict],
    feature_names: List[str] | None = None,
) -> List[Dict[str, object]]:
    feature_names = feature_names or DEFAULT_FEATURES
    rows: List[DriftRow] = []

    values: Dict[str, List[float]] = {f: [] for f in feature_names}
    for p in predictions:
        features = p.get("input_features") or {}
        for f in feature_names:
            if f in features:
                values[f].append(_safe_float(features.get(f), default=0.0))

    for f in feature_names:
        training_mean = _safe_float((baseline_means or {}).get(f), 0.0)
        current_mean = _mean(values[f]) if values.get(f) else 0.0
        denom = abs(training_mean) if abs(training_mean) > 1e-9 else 1.0
        drift_pct = ((current_mean - training_mean) / denom) * 100.0
        rows.append(
            DriftRow(
                feature=f,
                training_mean=training_mean,
                current_mean=current_mean,
                drift_pct=drift_pct,
                drift_flag=abs(drift_pct) >= 20.0,
            )
        )

    return [r.__dict__ for r in rows]


def overall_model_health(confidence_status: str, distribution_status: str, error_rate: float = 0.0) -> str:
    severity_rank = {"Healthy": 0, "Warning": 1, "Needs retraining": 2}
    status = "Healthy"
    if severity_rank.get(confidence_status, 0) >= 2 or severity_rank.get(distribution_status, 0) >= 2 or error_rate > 0.1:
        status = "Needs retraining"
    elif severity_rank.get(confidence_status, 0) >= 1 or severity_rank.get(distribution_status, 0) >= 1 or error_rate > 0.05:
        status = "Warning"
    return status
