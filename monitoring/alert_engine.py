from __future__ import annotations

from datetime import datetime
from typing import Dict, List


def _alert(level: str, title: str, detail: str, source: str) -> Dict[str, str]:
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "severity": level,
        "title": title,
        "detail": detail,
        "source": source,
    }


def generate_alerts(latest_prediction: dict | None, previous_prediction: dict | None, monitoring_summary: dict | None) -> List[Dict[str, str]]:
    alerts: List[Dict[str, str]] = []

    lp = latest_prediction or {}
    prev = previous_prediction or {}
    summary = monitoring_summary or {}

    features = lp.get("input_features") or {}
    egfr = features.get("egfr")
    try:
        if egfr is not None and float(egfr) < 30:
            alerts.append(_alert("CRITICAL", "Severe renal impairment", "eGFR below 30 detected in latest case.", "clinical_rules"))
    except Exception:
        pass

    label = str(lp.get("predicted_label") or "").strip().lower()
    if label in {"3", "high risk", "high cognitive risk"}:
        alerts.append(_alert("CRITICAL", "High risk prediction", "Latest prediction is high risk class.", "risk_model"))

    if prev:
        prev_label = str(prev.get("predicted_label") or "").strip().lower()
        if prev_label in {"1", "low risk", "low cognitive risk", "2", "moderate risk", "moderate cognitive risk"} and label in {"3", "high risk", "high cognitive risk"}:
            alerts.append(_alert("WARNING", "Risk escalation", "Patient trajectory escalated to high risk.", "longitudinal"))

    confidence_drift = summary.get("confidence_drift") or {}
    if confidence_drift.get("status") in {"Warning", "Needs retraining"}:
        alerts.append(_alert("INFO", "Confidence drift observed", "Model confidence trend declined vs baseline.", "ml_monitoring"))

    return alerts
