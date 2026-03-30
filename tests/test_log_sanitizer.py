import pytest

from core.log_sanitizer import sanitize_prediction_input


def test_allowed_fields_unchanged():
    data = {"age": 65, "gender": 1, "education_years": 12}
    out = sanitize_prediction_input(data)
    assert out["age"] == 65
    assert out["gender"] == 1
    assert out["education_years"] == 12
    assert out["feature_count"] == 3


def test_lab_values_masked():
    data = {"creatinine": 2.3, "egfr": 40, "bun": 55}
    out = sanitize_prediction_input(data)
    # egfr 40 -> low
    assert out.get("egfr_range") == "low"
    # creatinine 2.3 -> high (above 1.3)
    assert out.get("creatinine_range") == "high"
    # bun 55 -> high
    assert out.get("bun_range") == "high"
    assert out["feature_count"] == 3


def test_no_raw_values_appear():
    data = {"creatinine": 2.3}
    out = sanitize_prediction_input(data)
    # Ensure numeric raw value not present
    vals = list(out.values())
    assert 2.3 not in vals


def test_missing_and_invalid_values():
    # missing input
    out = sanitize_prediction_input({})
    assert out["feature_count"] == 0

    # invalid values handled safely
    out2 = sanitize_prediction_input({"egfr": "not_a_number", "creatinine": "x"})
    assert out2.get("egfr_range") == "unknown"
    assert out2.get("creatinine_range") == "unknown"
