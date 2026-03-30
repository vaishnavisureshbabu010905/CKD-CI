"""
Production-oriented standalone end-to-end ML pipeline for CKD-CI.

Adds:
- Input schema and clinical range validation
- Optional external dataset validation and drift reporting
- Calibration diagnostics (Brier score per class)
- Class-1 threshold tuning for recall improvement
- Artifact metadata and run traceability
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import uuid
import warnings
from datetime import datetime

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

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

RISK_LABELS = {
    0: "No Cognitive Risk",
    1: "Low Cognitive Risk",
    2: "Moderate Cognitive Risk",
    3: "High Cognitive Risk",
}

RANDOM_STATE = 42
DATASET_SIZE = 2000
TEST_SIZE = 0.2
RESULTS_DIR = "results"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CKD-CI production-style training pipeline")
    parser.add_argument("--external-data", default="", help="Optional external CSV for validation/drift checks")
    parser.add_argument("--dataset-size", type=int, default=DATASET_SIZE)
    return parser.parse_args()


def generate_synthetic_ckd_dataset(n_samples: int = 2000, random_state: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(random_state)

    age = np.clip(rng.normal(62, 12, n_samples), 20, 90)
    education_years = np.clip(rng.normal(12, 3, n_samples), 2, 22)
    gender = rng.integers(0, 2, n_samples)

    egfr = np.clip(rng.normal(58, 20, n_samples), 8, 130)
    creatinine = np.clip(1.25 + (75 - egfr) / 95 + rng.normal(0, 0.2, n_samples), 0.5, 6.5)
    bun = np.clip(17 + (75 - egfr) / 3.2 + rng.normal(0, 5, n_samples), 5, 95)
    uacr = np.clip(rng.lognormal(mean=4.0, sigma=0.9, size=n_samples), 5, 2500)
    hemoglobin = np.clip(13.5 - (75 - egfr) / 22 + rng.normal(0, 0.9, n_samples), 7, 18)
    albumin = np.clip(4.2 - (75 - egfr) / 95 + rng.normal(0, 0.3, n_samples), 2.2, 5.2)
    hscrp = np.clip(rng.lognormal(mean=0.3, sigma=0.65, size=n_samples), 0.1, 45)
    potassium = np.clip(rng.normal(4.2, 0.45, n_samples), 2.7, 6.8)
    phosphate = np.clip(rng.normal(3.6 + (65 - egfr) / 55, 0.5, n_samples), 2.0, 8.0)
    calcium = np.clip(rng.normal(9.3, 0.45, n_samples), 7.8, 11.2)
    systolic_bp = np.clip(rng.normal(130 + (65 - egfr) / 2.5, 14, n_samples), 90, 220)
    bmi = np.clip(rng.normal(27.5, 4.8, n_samples), 16, 48)

    diabetes = rng.binomial(1, p=np.clip(0.22 + (age - 50) / 120, 0.05, 0.65), size=n_samples)
    hypertension = rng.binomial(1, p=np.clip(0.33 + (age - 45) / 95, 0.1, 0.85), size=n_samples)
    cvd = rng.binomial(1, p=np.clip(0.12 + (age - 50) / 145, 0.03, 0.55), size=n_samples)

    risk_score = (
        0.035 * (age - 55)
        + 0.021 * (bun - 20)
        + 0.30 * (creatinine - 1.1)
        + 0.015 * (uacr / 100)
        + 0.22 * diabetes
        + 0.17 * hypertension
        + 0.13 * cvd
        - 0.042 * (egfr - 60)
        - 0.095 * (hemoglobin - 12)
        - 0.070 * (education_years - 10)
        - 0.17 * (albumin - 3.8)
        + rng.normal(0, 0.55, n_samples)
    )

    q1, q2, q3 = np.quantile(risk_score, [0.25, 0.5, 0.75])
    cognitive_risk = np.digitize(risk_score, bins=[q1, q2, q3])

    ckd_stage = np.where(
        egfr >= 90,
        "G1",
        np.where(egfr >= 60, "G2", np.where(egfr >= 45, "G3a", np.where(egfr >= 30, "G3b", np.where(egfr >= 15, "G4", "G5")))),
    )

    return pd.DataFrame(
        {
            "age": age,
            "education_years": education_years,
            "gender": gender,
            "eGFR": egfr,
            "creatinine": creatinine,
            "bun": bun,
            "uacr": uacr,
            "hemoglobin": hemoglobin,
            "albumin": albumin,
            "hsCRP": hscrp,
            "potassium": potassium,
            "phosphate": phosphate,
            "calcium": calcium,
            "systolic_bp": systolic_bp,
            "bmi": bmi,
            "diabetes": diabetes,
            "hypertension": hypertension,
            "cvd": cvd,
            "CKD_stage": ckd_stage,
            "cognitive_risk": cognitive_risk,
        }
    )


def validate_schema(df: pd.DataFrame, require_target: bool) -> tuple[bool, list[str]]:
    required = FEATURE_COLUMNS + (["cognitive_risk"] if require_target else [])
    issues = []

    for col in required:
        if col not in df.columns:
            issues.append(f"Missing column: {col}")

    for col in FEATURE_COLUMNS:
        if col in df.columns:
            low, high = CLINICAL_RANGES[col]
            out_count = int(((df[col] < low) | (df[col] > high)).sum())
            if out_count > 0:
                issues.append(f"Out-of-range values in {col}: {out_count}")

    if require_target and "cognitive_risk" in df.columns:
        invalid_target = int((~df["cognitive_risk"].isin([0, 1, 2, 3])).sum())
        if invalid_target > 0:
            issues.append(f"Invalid cognitive_risk labels: {invalid_target}")

    return (len(issues) == 0), issues


def compute_drift_report(reference_df: pd.DataFrame, external_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in FEATURE_COLUMNS:
        ref_mean = float(reference_df[col].mean())
        ext_mean = float(external_df[col].mean())
        ref_std = float(reference_df[col].std() + 1e-9)
        z_shift = abs(ext_mean - ref_mean) / ref_std
        rows.append(
            {
                "feature": col,
                "reference_mean": ref_mean,
                "external_mean": ext_mean,
                "mean_shift_zscore": z_shift,
                "drift_flag": z_shift >= 0.75,
            }
        )

    return pd.DataFrame(rows).sort_values("mean_shift_zscore", ascending=False)


def evaluate_model(model_name: str, model, x_test: np.ndarray, y_test: pd.Series) -> tuple[dict, np.ndarray, np.ndarray]:
    y_pred = model.predict(x_test)
    y_pred_proba = model.predict_proba(x_test)

    metrics = {
        "Model": model_name,
        "Accuracy": accuracy_score(y_test, y_pred),
        "AUC-ROC": roc_auc_score(y_test, y_pred_proba, multi_class="ovr"),
        "Precision (Weighted)": precision_score(y_test, y_pred, average="weighted", zero_division=0),
        "Recall (Weighted)": recall_score(y_test, y_pred, average="weighted", zero_division=0),
        "F1-Score (Weighted)": f1_score(y_test, y_pred, average="weighted", zero_division=0),
        "Log Loss": log_loss(y_test, y_pred_proba),
    }
    return metrics, y_pred, y_pred_proba


def tune_class1_threshold(y_true: pd.Series, y_proba: np.ndarray, base_preds: np.ndarray) -> tuple[float, dict]:
    best_threshold = 0.25
    best_recall = -1.0
    best_metrics = {}

    for thr in np.arange(0.15, 0.51, 0.02):
        tuned_preds = base_preds.copy()
        tuned_preds[y_proba[:, 1] >= thr] = 1

        class1_true = (y_true == 1).astype(int)
        class1_pred = (tuned_preds == 1).astype(int)

        rec = recall_score(class1_true, class1_pred, zero_division=0)
        prec = precision_score(class1_true, class1_pred, zero_division=0)
        f1 = f1_score(class1_true, class1_pred, zero_division=0)

        if rec > best_recall:
            best_recall = rec
            best_threshold = float(thr)
            best_metrics = {
                "class1_recall": float(rec),
                "class1_precision": float(prec),
                "class1_f1": float(f1),
            }

    return best_threshold, best_metrics


def compute_calibration_metrics(y_true: pd.Series, y_proba: np.ndarray) -> pd.DataFrame:
    rows = []
    for k in [0, 1, 2, 3]:
        y_bin = (y_true == k).astype(int)
        rows.append(
            {
                "class": k,
                "label": RISK_LABELS[k],
                "brier_score": brier_score_loss(y_bin, y_proba[:, k]),
            }
        )
    return pd.DataFrame(rows)


def make_run_config_hash(config: dict) -> str:
    blob = json.dumps(config, sort_keys=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:12]


def main() -> None:
    args = parse_args()
    np.random.seed(RANDOM_STATE)

    run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
    os.makedirs(RESULTS_DIR, exist_ok=True)

    print("\n" + "=" * 80)
    print("CKD-CI: PRODUCTION-ORIENTED COMPLETE ML PIPELINE")
    print("=" * 80)
    print(f"Run ID: {run_id}")

    print("\n[STEP 1] GENERATING TRAINING DATA")
    df = generate_synthetic_ckd_dataset(n_samples=args.dataset_size, random_state=RANDOM_STATE)
    ok, issues = validate_schema(df, require_target=True)
    if not ok:
        raise ValueError("Training data validation failed: " + " | ".join(issues))
    print(f"[OK] Rows: {len(df)}, Columns: {df.shape[1]}")

    print("\n[STEP 2] PREPROCESSING")
    x = df[FEATURE_COLUMNS].copy()
    y = df["cognitive_risk"].copy()
    x = x.fillna(x.median(numeric_only=True))

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )

    smote = SMOTE(k_neighbors=3, random_state=RANDOM_STATE)
    x_train_resampled, y_train_resampled = smote.fit_resample(x_train, y_train)

    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train_resampled)
    x_test_scaled = scaler.transform(x_test)

    print(f"[OK] Train shape after SMOTE: {x_train_scaled.shape}")
    print(f"[OK] Test shape: {x_test_scaled.shape}")

    print("\n[STEP 3] FEATURE IMPORTANCE")
    rf_selector = RandomForestClassifier(n_estimators=140, random_state=RANDOM_STATE, n_jobs=-1)
    rf_selector.fit(x_train_resampled, y_train_resampled)
    feature_importance_df = pd.DataFrame({"feature": FEATURE_COLUMNS, "importance": rf_selector.feature_importances_}).sort_values(
        "importance", ascending=False
    )
    print(feature_importance_df.head(12).to_string(index=False))

    print("\n[STEP 4] MODEL TRAINING")
    models = {
        "Logistic Regression": LogisticRegression(max_iter=1200, random_state=RANDOM_STATE, class_weight="balanced"),
        "Random Forest": RandomForestClassifier(
            n_estimators=220, max_depth=14, random_state=RANDOM_STATE, n_jobs=-1, class_weight="balanced_subsample"
        ),
        "XGBoost": XGBClassifier(
            n_estimators=220,
            max_depth=6,
            learning_rate=0.06,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=RANDOM_STATE,
            eval_metric="mlogloss",
        ),
        "SVM": SVC(kernel="rbf", probability=True, random_state=RANDOM_STATE, class_weight="balanced"),
    }

    trained_models = {}
    all_eval = {}
    rows = []

    for model_name, model in models.items():
        print(f"  - Training {model_name}...")
        model.fit(x_train_scaled, y_train_resampled)
        trained_models[model_name] = model
        metrics, y_pred, y_proba = evaluate_model(model_name, model, x_test_scaled, y_test)
        rows.append(metrics)
        all_eval[model_name] = {"y_pred": y_pred, "y_proba": y_proba, "metrics": metrics}

    comparison_df = pd.DataFrame(rows).sort_values("AUC-ROC", ascending=False)
    print("\n[STEP 5] EVALUATION RESULTS")
    print(comparison_df.to_string(index=False))

    best_model_name = str(comparison_df.iloc[0]["Model"])
    best_model = trained_models[best_model_name]
    best_y_pred = all_eval[best_model_name]["y_pred"]
    best_y_proba = all_eval[best_model_name]["y_proba"]

    print("\n[STEP 6] CLASS-1 THRESHOLD TUNING")
    best_thr, class1_metrics = tune_class1_threshold(y_test, best_y_proba, best_y_pred)
    print(f"[OK] Selected class-1 threshold: {best_thr:.2f}")
    print(f"[OK] Class-1 metrics: {class1_metrics}")

    print("\n[STEP 7] CALIBRATION METRICS")
    calibration_df = compute_calibration_metrics(y_test, best_y_proba)
    print(calibration_df.to_string(index=False))

    cm = confusion_matrix(y_test, best_y_pred)

    print("\n[STEP 8] EXTERNAL VALIDATION + DRIFT")
    drift_df = pd.DataFrame()
    external_eval = {}
    if args.external_data:
        if not os.path.exists(args.external_data):
            raise FileNotFoundError(f"External data not found: {args.external_data}")

        ext_df = pd.read_csv(args.external_data)
        ok_ext, ext_issues = validate_schema(ext_df, require_target=False)
        if not ok_ext:
            print("[WARN] External data schema/range issues:")
            for issue in ext_issues:
                print(f"  - {issue}")

        for col in FEATURE_COLUMNS:
            if col not in ext_df.columns:
                ext_df[col] = np.nan
        ext_x = ext_df[FEATURE_COLUMNS].fillna(x_train.median(numeric_only=True))
        ext_scaled = scaler.transform(ext_x)

        ext_pred = best_model.predict(ext_scaled)
        ext_proba = best_model.predict_proba(ext_scaled)

        external_eval = {
            "rows_scored": int(len(ext_df)),
            "predicted_distribution": pd.Series(ext_pred).value_counts().sort_index().to_dict(),
            "avg_confidence": float(np.max(ext_proba, axis=1).mean()),
        }

        drift_df = compute_drift_report(x_train_resampled[FEATURE_COLUMNS], ext_df[FEATURE_COLUMNS].fillna(x_train.median()))
        print(f"[OK] External rows scored: {external_eval['rows_scored']}")
        print(f"[OK] Avg confidence: {external_eval['avg_confidence']:.3f}")
        print("[OK] Top drift features:")
        print(drift_df.head(8).to_string(index=False))
    else:
        print("[INFO] No external dataset supplied. Skipping external validation.")

    print("\n[STEP 9] SAVING ARTIFACTS")
    comparison_path = os.path.join(RESULTS_DIR, "model_comparison.csv")
    feature_path = os.path.join(RESULTS_DIR, "feature_importance.csv")
    calibration_path = os.path.join(RESULTS_DIR, "calibration_metrics.csv")
    drift_path = os.path.join(RESULTS_DIR, "drift_report.csv")

    model_path = os.path.join(RESULTS_DIR, "best_model.pkl")
    scaler_path = os.path.join(RESULTS_DIR, "scaler.pkl")
    bundle_path = os.path.join(RESULTS_DIR, "model_bundle.pkl")
    metadata_path = os.path.join(RESULTS_DIR, "run_metadata.json")

    comparison_df.to_csv(comparison_path, index=False)
    feature_importance_df.to_csv(feature_path, index=False)
    calibration_df.to_csv(calibration_path, index=False)
    if not drift_df.empty:
        drift_df.to_csv(drift_path, index=False)

    joblib.dump(best_model, model_path)
    joblib.dump(scaler, scaler_path)

    run_config = {
        "random_state": RANDOM_STATE,
        "dataset_size": int(args.dataset_size),
        "test_size": TEST_SIZE,
        "best_model": best_model_name,
        "class1_threshold": best_thr,
    }

    bundle = {
        "model": best_model,
        "scaler": scaler,
        "feature_columns": FEATURE_COLUMNS,
        "risk_labels": RISK_LABELS,
        "thresholds": {"class_1": best_thr},
        "run_id": run_id,
        "config_hash": make_run_config_hash(run_config),
        "created_utc": datetime.utcnow().isoformat() + "Z",
    }
    joblib.dump(bundle, bundle_path)

    metadata = {
        "run_id": run_id,
        "created_utc": datetime.utcnow().isoformat() + "Z",
        "config": run_config,
        "config_hash": make_run_config_hash(run_config),
        "best_model_metrics": all_eval[best_model_name]["metrics"],
        "class1_tuning": class1_metrics,
        "calibration": calibration_df.to_dict(orient="records"),
        "external_validation": external_eval,
        "artifacts": {
            "comparison": comparison_path,
            "feature_importance": feature_path,
            "calibration": calibration_path,
            "drift_report": drift_path if not drift_df.empty else "",
            "best_model": model_path,
            "scaler": scaler_path,
            "bundle": bundle_path,
        },
    }
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    top_features = feature_importance_df.head(15)
    axes[0].barh(top_features["feature"], top_features["importance"], color="#1f77b4")
    axes[0].set_title("Top Feature Importances")
    axes[0].invert_yaxis()

    heatmap = axes[1].imshow(cm, cmap="Blues")
    axes[1].set_title("Confusion Matrix")
    axes[1].set_xlabel("Predicted")
    axes[1].set_ylabel("Actual")
    plt.colorbar(heatmap, ax=axes[1])
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            axes[1].text(j, i, str(cm[i, j]), ha="center", va="center", color="black")

    plt.tight_layout()
    plot_path = os.path.join(RESULTS_DIR, "evaluation_summary.png")
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"[OK] Saved comparison: {comparison_path}")
    print(f"[OK] Saved feature importances: {feature_path}")
    print(f"[OK] Saved calibration: {calibration_path}")
    if not drift_df.empty:
        print(f"[OK] Saved drift report: {drift_path}")
    print(f"[OK] Saved model: {model_path}")
    print(f"[OK] Saved scaler: {scaler_path}")
    print(f"[OK] Saved model bundle: {bundle_path}")
    print(f"[OK] Saved metadata: {metadata_path}")
    print(f"[OK] Saved plot: {plot_path}")

    print("\n" + "=" * 80)
    print("PIPELINE STATUS: COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
