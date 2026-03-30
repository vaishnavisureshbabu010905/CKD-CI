from __future__ import annotations

from typing import Dict


PROFILES: Dict[str, Dict[str, float | int]] = {
    "low": {
        "age": 50,
        "education_years": 14,
        "gender": 0,
        "egfr": 98.0,
        "creatinine": 0.8,
        "bun": 13.0,
        "uacr": 15.0,
        "hemoglobin": 14.1,
        "albumin": 4.3,
        "hscrp": 1.1,
        "bmi": 23.0,
        "potassium": 4.0,
        "phosphorus": 3.2,
        "calcium": 9.5,
        "systolic_bp": 118,
        "diabetes": 0,
        "hypertension": 0,
        "cvd": 0,
    },
    "moderate": {
        "age": 66,
        "education_years": 11,
        "gender": 1,
        "egfr": 56.0,
        "creatinine": 1.5,
        "bun": 29.0,
        "uacr": 320.0,
        "hemoglobin": 11.5,
        "albumin": 3.4,
        "hscrp": 4.3,
        "bmi": 28.0,
        "potassium": 4.9,
        "phosphorus": 4.7,
        "calcium": 8.9,
        "systolic_bp": 150,
        "diabetes": 1,
        "hypertension": 1,
        "cvd": 0,
    },
    "high": {
        "age": 78,
        "education_years": 8,
        "gender": 1,
        "egfr": 24.0,
        "creatinine": 3.0,
        "bun": 58.0,
        "uacr": 1600.0,
        "hemoglobin": 9.2,
        "albumin": 2.8,
        "hscrp": 9.4,
        "bmi": 31.0,
        "potassium": 5.8,
        "phosphorus": 6.3,
        "calcium": 8.0,
        "systolic_bp": 172,
        "diabetes": 1,
        "hypertension": 1,
        "cvd": 1,
    },
}


def generate_profile(profile: str) -> Dict[str, float | int]:
    key = str(profile or "").strip().lower()
    if key not in PROFILES:
        key = "moderate"
    return dict(PROFILES[key])
