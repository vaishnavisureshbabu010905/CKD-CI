from core import metrics


def reset_metrics():
    # Reset internal counters for test isolation
    metrics._predictions_total = 0
    metrics._prediction_errors = 0
    metrics._total_confidence = 0.0
    metrics._class_distribution.clear()


def test_increment_prediction_and_distribution():
    reset_metrics()
    metrics.increment_prediction(1, 0.8)
    metrics.increment_prediction(2, 0.6)
    metrics.increment_prediction(1, 0.9)
    m = metrics.get_metrics()
    assert m["predictions_total"] == 3
    assert m["errors"] == 0
    # avg confidence = (0.8+0.6+0.9)/3
    assert round(m["avg_confidence"], 3) == round((0.8 + 0.6 + 0.9) / 3, 3)
    assert m["class_distribution"]["1"] == 2
    assert m["class_distribution"]["2"] == 1


def test_increment_error():
    reset_metrics()
    metrics.increment_error()
    metrics.increment_error()
    m = metrics.get_metrics()
    assert m["errors"] == 2
