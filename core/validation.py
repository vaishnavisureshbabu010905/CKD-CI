from typing import Dict, List, Any, Optional
import math
import pandas as pd

FEATURE_COLUMNS = [
    "age",
    "education_years",
    "gender",
    "eGFR",
    "creatinine",
    "bun",
    "uacr",
    "hemoglobin",
    "albumin",
    "hsCRP",
    "potassium",
    "phosphate",
    "calcium",
    "systolic_bp",
    "bmi",
    "diabetes",
    "hypertension",
    "cvd",
]

# Canonical clinical guardrails matching trained model bundle
CLINICAL_RANGES = {
    "age": (20, 95),
    "education_years": (0, 25),
    "gender": (0, 1),
    "eGFR": (0, 150),
    "creatinine": (0.2, 10),
    "bun": (2, 150),
    "uacr": (0, 5000),
    "hemoglobin": (5, 20),
    "albumin": (1.5, 6),
    "hsCRP": (0, 100),
    "potassium": (2, 8),
    "phosphate": (1, 10),
    "calcium": (6, 13),
    "systolic_bp": (70, 260),
    "bmi": (10, 60),
    "diabetes": (0, 1),
    "hypertension": (0, 1),
    "cvd": (0, 1),
}

ALIAS_MAP = {
    "egfr": "eGFR",
    "e_gfr": "eGFR",
    "phosphorus": "phosphate",
    "phosphate": "phosphate",
    "hscrp": "hsCRP",
    "hs_crp": "hsCRP",
    "educationyears": "education_years",
    "education_years": "education_years",
    "systolicbp": "systolic_bp",
    "systolic_bp": "systolic_bp",
}


def normalize_feature_dict(features: Dict[str, Any]) -> Dict[str, Any]:
    """Map any casing/synonym variants to canonical feature names."""
    if not isinstance(features, dict):
        return {}
    canonical = {}
    for k, v in features.items():
        k_str = str(k).strip()
        lower_k = k_str.lower()
        target_key = ALIAS_MAP.get(lower_k, k_str)
        canonical[target_key] = v
    return canonical


def validate_features(features: Dict[str, object]) -> List[str]:
    """Return list of validation issues; empty list means valid."""
    issues = []
    if not isinstance(features, dict):
        return ["features must be an object/dictionary"]

    normalized = normalize_feature_dict(features)

    # Check for missing keys
    for key in CLINICAL_RANGES.keys():
        if key not in normalized:
            issues.append(f"missing_feature:{key}")

    # Value checks
    for key, (low, high) in CLINICAL_RANGES.items():
        if key not in normalized:
            continue
        val = normalized.get(key)
        try:
            if val is None:
                issues.append(f"null_value:{key}")
                continue
            v = float(val)
            if math.isnan(v):
                issues.append(f"nan_value:{key}")
                continue
            if v < low or v > high:
                issues.append(f"out_of_range:{key}")
        except Exception:
            issues.append(f"invalid_type:{key}")

    return issues


def validate_columns(df: pd.DataFrame) -> None:
    """Validate DataFrame contains all required feature columns."""
    missing = [col for col in FEATURE_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def validate_ranges(df: pd.DataFrame) -> List[str]:
    """Flag rows exceeding standard clinical bounds."""
    issues = []
    for col, (low, high) in CLINICAL_RANGES.items():
        if col in df.columns:
            out_count = int(((df[col] < low) | (df[col] > high)).sum())
            if out_count > 0:
                issues.append(f"{col}: {out_count} rows out of range [{low}, {high}]")
    return issues
