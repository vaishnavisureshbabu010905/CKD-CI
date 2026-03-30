"""In-memory metrics for basic observability.

Not a replacement for Prometheus/OTel; simple counters for demo purposes.
"""
from __future__ import annotations
from threading import Lock
from typing import Dict

_lock = Lock()
_predictions_total = 0
_prediction_errors = 0
_total_confidence = 0.0
_class_distribution: Dict[str, int] = {}


def increment_prediction(prediction_class, confidence: float) -> None:
    global _predictions_total, _total_confidence, _class_distribution
    with _lock:
        _predictions_total += 1
        try:
            _total_confidence += float(confidence or 0.0)
        except Exception:
            pass
        key = str(prediction_class)
        _class_distribution[key] = _class_distribution.get(key, 0) + 1


def increment_error() -> None:
    global _prediction_errors
    with _lock:
        _prediction_errors += 1


def get_metrics() -> Dict:
    with _lock:
        avg_conf = (_total_confidence / _predictions_total) if _predictions_total > 0 else 0.0
        return {
            "predictions_total": _predictions_total,
            "errors": _prediction_errors,
            "avg_confidence": round(avg_conf, 4),
            "class_distribution": dict(_class_distribution),
        }


def get_metrics_prometheus() -> str:
    """Return a simple Prometheus exposition format string."""
    m = get_metrics()
    lines = []
    lines.append(f"# HELP ckdci_predictions_total Total number of predictions")
    lines.append(f"# TYPE ckdci_predictions_total counter")
    lines.append(f"ckdci_predictions_total {m.get('predictions_total', 0)}")
    lines.append(f"# HELP ckdci_prediction_errors Total prediction errors")
    lines.append(f"# TYPE ckdci_prediction_errors counter")
    lines.append(f"ckdci_prediction_errors {m.get('errors', 0)}")
    lines.append(f"# HELP ckdci_avg_confidence Average confidence of predictions")
    lines.append(f"# TYPE ckdci_avg_confidence gauge")
    lines.append(f"ckdci_avg_confidence {m.get('avg_confidence', 0.0)}")
    # class distribution as labeled gauges
    cd = m.get("class_distribution", {}) or {}
    for k, v in cd.items():
        lines.append(f"# HELP ckdci_class_count_{k} Class distribution count for class {k}")
        lines.append(f"# TYPE ckdci_class_count_{k} gauge")
        lines.append(f"ckdci_class_count{{class=\"{k}\"}} {v}")
    return "\n".join(lines) + "\n"
