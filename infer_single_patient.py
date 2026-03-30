"""
Run inference using CKD-CI model artifacts.

Usage examples:
  .venv312\\Scripts\\python.exe infer_single_patient.py --input sample_patient.csv
  .venv312\\Scripts\\python.exe infer_single_patient.py --input sample_patient.csv --output results/predictions.csv
"""

from __future__ import annotations

import argparse
import os

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

DEFAULT_RISK_LABELS = {
    0: "No Cognitive Risk",
    1: "Low Cognitive Risk",
    2: "Moderate Cognitive Risk",
    3: "High Cognitive Risk",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CKD-CI model inference from CSV input.")
    parser.add_argument("--input", required=True, help="Path to input CSV with required features.")
    parser.add_argument("--bundle", default=os.path.join("results", "model_bundle.pkl"), help="Path to model bundle.")
    parser.add_argument("--model", default=os.path.join("results", "best_model.pkl"), help="Fallback model path.")
    parser.add_argument("--scaler", default=os.path.join("results", "scaler.pkl"), help="Fallback scaler path.")
    parser.add_argument("--output", default=os.path.join("results", "predictions.csv"), help="Path to save prediction CSV.")
    return parser.parse_args()


def validate_columns(df: pd.DataFrame) -> None:
    missing = [col for col in FEATURE_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def validate_ranges(df: pd.DataFrame) -> list[str]:
    issues = []
    for col, (low, high) in CLINICAL_RANGES.items():
        out_count = int(((df[col] < low) | (df[col] > high)).sum())
        if out_count > 0:
            issues.append(f"{col}: {out_count} rows out of range [{low}, {high}]")
    return issues


def load_artifacts(bundle_path: str, model_path: str, scaler_path: str):
    try:
        import joblib
    except Exception:
        raise RuntimeError("joblib is required to load model artifacts")

    if os.path.exists(bundle_path):
        bundle = joblib.load(bundle_path)
        return (
            bundle["model"],
            bundle["scaler"],
            bundle.get("feature_columns", FEATURE_COLUMNS),
            bundle.get("risk_labels", DEFAULT_RISK_LABELS),
            bundle.get("thresholds", {}),
        )

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    if not os.path.exists(scaler_path):
        raise FileNotFoundError(f"Scaler file not found: {scaler_path}")

    return joblib.load(model_path), joblib.load(scaler_path), FEATURE_COLUMNS, DEFAULT_RISK_LABELS, {}


def apply_thresholds(pred_class: pd.Series, pred_proba, thresholds: dict) -> pd.Series:
    out = pred_class.copy()
    class1_thr = thresholds.get("class_1")
    if class1_thr is not None:
        out[pred_proba[:, 1] >= float(class1_thr)] = 1
    return out


def main() -> None:
    args = parse_args()

    if not os.path.exists(args.input):
        raise FileNotFoundError(f"Input CSV not found: {args.input}")

    df = pd.read_csv(args.input)
    validate_columns(df)

    range_issues = validate_ranges(df)
    if range_issues:
        print("[WARN] Input range issues found:")
        for issue in range_issues:
            print(f"  - {issue}")

    model, scaler, feature_columns, risk_labels, thresholds = load_artifacts(
        args.bundle, args.model, args.scaler
    )

    x = df[feature_columns].copy()
    x = x.fillna(x.median(numeric_only=True))
    x_scaled = scaler.transform(x)

    pred_class = pd.Series(model.predict(x_scaled))
    pred_proba = model.predict_proba(x_scaled)
    pred_class = apply_thresholds(pred_class, pred_proba, thresholds)

    out = df.copy()
    out["predicted_class"] = pred_class.values
    out["predicted_label"] = [risk_labels[int(c)] for c in pred_class.values]

    for i in range(pred_proba.shape[1]):
        out[f"prob_class_{i}"] = pred_proba[:, i]

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    out.to_csv(args.output, index=False)

    print("Inference complete.")
    print(f"Input rows: {len(df)}")
    print(f"Saved predictions: {args.output}")
    print("Class counts:")
    print(out["predicted_label"].value_counts().to_string())


if __name__ == "__main__":
    main()
