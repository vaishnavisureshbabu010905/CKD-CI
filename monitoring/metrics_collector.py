from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client.core import CollectorRegistry
from core.metrics import get_metrics
from typing import Dict

registry = CollectorRegistry()

prediction_counter = Counter("ckdci_predictions_total", "Total predictions", registry=registry)
prediction_latency = Histogram("ckdci_prediction_latency_seconds", "Prediction latency seconds", registry=registry)
api_requests = Counter("ckdci_api_requests_total", "Total API requests", registry=registry)
errors = Counter("ckdci_errors_total", "Total errors", registry=registry)
active_model_gauge = Gauge("ckdci_active_model_version", "Active model version (as numeric hash)", registry=registry)


def observe_prediction(latency_seconds: float):
    prediction_counter.inc()
    prediction_latency.observe(latency_seconds)


def observe_error():
    errors.inc()


def metrics_text() -> bytes:
    # merge in core metrics as labels via a simple exposition
    return generate_latest(registry)
