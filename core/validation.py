from typing import Dict, List
import math

# Clinical guardrails — mirror UI ranges to ensure server-side validation
CLINICAL_RANGES = {
    "age": (20, 95),
    "gender": (0, 1),
    "egfr": (0, 150),
    "creatinine": (0.2, 10),
    "bun": (2, 150),
    "uacr": (0, 5000),
    "hemoglobin": (5, 20),
    "albumin": (1.5, 6),
    "potassium": (2, 8),
    "phosphorus": (1, 10),
    "calcium": (6, 13),
    "systolic_bp": (70, 260),
    "bmi": (10, 60),
    "diabetes": (0, 1),
    "hypertension": (0, 1),
    "cvd": (0, 1),
}


def validate_features(features: Dict[str, object]) -> List[str]:
    """Return list of validation issues; empty list means valid."""
    issues = []
    if not isinstance(features, dict):
        return ["features must be an object/dictionary"]

    # Check for missing keys
    for key in CLINICAL_RANGES.keys():
        if key not in features:
            issues.append(f"missing_feature:{key}")

    # Value checks
    for key, (low, high) in CLINICAL_RANGES.items():
        if key not in features:
            continue
        val = features.get(key)
        # Reject NaN or non-numeric where numeric expected (booleans allowed for 0/1)
        try:
            if val is None:
                issues.append(f"null_value:{key}")
                continue
            # convert booleans/strings to float if possible
            v = float(val)
            if math.isnan(v):
                issues.append(f"nan_value:{key}")
                continue
            if v < low or v > high:
                issues.append(f"out_of_range:{key}")
        except Exception:
            issues.append(f"invalid_type:{key}")

    return issues
