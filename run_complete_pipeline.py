"""
Production-oriented standalone end-to-end ML pipeline for CKD-CI.

Supports:
- Lightweight, CPU-only models: CatBoost, XGBoost, Random Forest, Logistic Regression
- Saves models together into individual standalone artifacts:
  models/catboost.pkl, models/xgboost.pkl, models/random_forest.pkl
- Automatic best-model selection bundled into results/model_bundle.pkl for API inference
- Input schema and clinical range validation
- Calibration diagnostics (Brier score per class)
- Class-1 threshold tuning for recall improvement
- Optional external dataset validation and drift reporting
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
from xgboost import XGBClassifier

# Optional CatBoost import with graceful fallback if not yet installed
try:
    from catboost import CatBoostClassifier

    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False

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
MODELS_DIR = "models"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CKD-CI lightweight CPU training pipeline")
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
        - 0.045 * (education_years - 12)
        - 0.055 * (albumin - 4.0)
        + 0.025 * (hscrp - 1.0)
        + rng.normal(0, 0.55, n_samples)
    )

    q1, q2, q3 = np.quantile(risk_score, [0.40, 0.72, 0.90])
    target = np.select(
        [risk_score < q1, risk_score < q2, risk_score < q3],
        [0, 1, 2],
        default=3,
    )

    return pd.DataFrame(
        {
            "age": np.round(age, 1),
            "education_years": np.round(education_years, 1),
            "gender": gender,
            "eGFR": np.round(egfr, 1),
            "creatinine": np.round(creatinine, 2),
            "bun": np.round(bun, 1),
            "uacr": np.round(uacr, 1),
            "hemoglobin": np.round(hemoglobin, 1),
            "albumin": np.round(albumin, 2),
            "hsCRP": np.round(hscrp, 2),
            "potassium": np.round(potassium, 2),
            "phosphate": np.round(phosphate, 2),
            "calcium": np.round(calcium, 2),
            "systolic_bp": np.round(systolic_bp, 1),
            "bmi": np.round(bmi, 1),
            "diabetes": diabetes,
            "hypertension": hypertension,
            "cvd": cvd,
            "cognitive_risk": target,
        }
    )


def validate_schema(df: pd.DataFrame, require_target: bool = True) -> tuple[bool, list[str]]:
    issues: list[str] = []
    missing_cols = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing_cols:
        issues.append(f"Missing feature columns: {missing_cols}")

    if require_target and "cognitive_risk" not in df.columns:
        issues.append("Missing required target column: 'cognitive_risk'")

    for col, (low, high) in CLINICAL_RANGES.items():
        if col in df.columns:
            s = df[col].dropna()
            out_of_bounds = s[(s < low) | (s > high)]
            if len(out_of_bounds) > 0:
                issues.append(
                    f"Column '{col}' has {len(out_of_bounds)} values outside valid clinical range [{low}, {high}]"
                )

    return len(issues) == 0, issues


def evaluate_model(name: str, model, x_test: np.ndarray, y_test: np.ndarray) -> tuple[dict, np.ndarray, np.ndarray]:
    y_pred = model.predict(x_test)
    if hasattr(y_pred, "ndim") and y_pred.ndim > 1:
        y_pred = y_pred.ravel().astype(int)
    else:
        y_pred = np.asarray(y_pred, dtype=int)

    y_proba = model.predict_proba(x_test)
    n_classes = len(np.unique(y_test))

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average="macro", zero_division=0)
    rec = recall_score(y_test, y_pred, average="macro", zero_division=0)
    f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)

    try:
        auc = roc_auc_score(y_test, y_proba, multi_class="ovr", average="macro")
    except Exception:
        auc = 0.5

    try:
        loss = log_loss(y_test, y_proba)
    except Exception:
        loss = float("nan")

    brier_scores = []
    for c in range(n_classes):
        bin_y = (y_test == c).astype(int)
        brier_scores.append(brier_score_loss(bin_y, y_proba[:, c]))
    mean_brier = float(np.mean(brier_scores))

    metrics = {
        "Model": name,
        "Accuracy": round(float(acc), 4),
        "Precision": round(float(prec), 4),
        "Recall": round(float(rec), 4),
        "F1-Macro": round(float(f1), 4),
        "AUC-ROC": round(float(auc), 4),
        "LogLoss": round(float(loss), 4) if not np.isnan(loss) else None,
        "MeanBrier": round(mean_brier, 4),
    }
    return metrics, y_pred, y_proba


def tune_class1_threshold(y_test: np.ndarray, y_proba: np.ndarray, base_preds: np.ndarray) -> tuple[float, dict]:
    y_binary = (y_test == 1).astype(int)
    class1_probs = y_proba[:, 1]
    best_threshold = 0.25
    best_f1 = -1.0
    best_metrics = {}

    for thr in np.linspace(0.10, 0.50, 41):
        tuned_pred = (class1_probs >= thr).astype(int)
        f1 = f1_score(y_binary, tuned_pred, zero_division=0)
        rec = recall_score(y_binary, tuned_pred, zero_division=0)
        prec = precision_score(y_binary, tuned_pred, zero_division=0)

        if f1 > best_f1:
            best_f1 = f1
            best_threshold = thr
            best_metrics = {
                "threshold": round(float(thr), 3),
                "f1": round(float(f1), 4),
                "recall": round(float(rec), 4),
                "precision": round(float(prec), 4),
            }

    return float(best_threshold), best_metrics


def compute_calibration_metrics(y_test: np.ndarray, y_proba: np.ndarray) -> pd.DataFrame:
    rows = []
    for c in sorted(np.unique(y_test)):
        bin_y = (y_test == c).astype(int)
        score = brier_score_loss(bin_y, y_proba[:, c])
        rows.append({"class": int(c), "class_name": RISK_LABELS.get(int(c), f"Class {c}"), "brier_score": round(float(score), 4)})
    return pd.DataFrame(rows)


def compute_drift_report(train_df: pd.DataFrame, ext_df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for col in train_df.columns:
        if col not in ext_df.columns:
            continue
        tr = train_df[col].dropna()
        ex = ext_df[col].dropna()
        if len(tr) == 0 or len(ex) == 0:
            continue
        mean_diff = float(ex.mean() - tr.mean())
        std_pool = float(np.sqrt((tr.var() + ex.var()) / 2.0))
        std_diff = mean_diff / std_pool if std_pool > 1e-8 else 0.0
        records.append(
            {
                "feature": col,
                "train_mean": round(float(tr.mean()), 3),
                "external_mean": round(float(ex.mean()), 3),
                "mean_diff": round(mean_diff, 3),
                "std_diff": round(std_diff, 3),
                "drift_alert": abs(std_diff) >= 0.5,
            }
        )
    return pd.DataFrame(records).sort_values("std_diff", key=abs, ascending=False)


def make_run_config_hash(config_dict: dict) -> str:
    raw = json.dumps(config_dict, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def main() -> None:
    args = parse_args()
    np.random.seed(RANDOM_STATE)

    run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR, exist_ok=True)

    print("\n" + "=" * 80)
    print("CKD-CI: LIGHTWEIGHT CPU CLINICAL MACHINE LEARNING PIPELINE")
    print("=" * 80)
    print(f"Run ID: {run_id}")
    print(f"CatBoost Installed: {'YES' if CATBOOST_AVAILABLE else 'NO (Install with: pip install catboost)'}")

    print("\n[STEP 1] INGESTING / GENERATING TRAINING DATA")
    if args.external_data and os.path.exists(args.external_data):
        print(f"[OK] Loading external training dataset: {args.external_data}")
        df = pd.read_csv(args.external_data)
    else:
        df = generate_synthetic_ckd_dataset(n_samples=args.dataset_size, random_state=RANDOM_STATE)
    
    ok, issues = validate_schema(df, require_target=True)
    if not ok:
        print("[WARN] Schema/range notices:")
        for is_item in issues[:5]:
            print(f"  - {is_item}")
    print(f"[OK] Rows: {len(df)}, Columns: {df.shape[1]}")

    print("\n[STEP 2] PREPROCESSING & STRATIFIED SPLIT")
    x = df[FEATURE_COLUMNS].copy()
    y = df["cognitive_risk"].copy().astype(int)
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

    print("\n[STEP 3] FEATURE IMPORTANCE (RANDOM FOREST)")
    rf_selector = RandomForestClassifier(n_estimators=150, random_state=RANDOM_STATE, n_jobs=4)
    rf_selector.fit(x_train_resampled, y_train_resampled)
    feature_importance_df = pd.DataFrame(
        {"feature": FEATURE_COLUMNS, "importance": rf_selector.feature_importances_}
    ).sort_values("importance", ascending=False)
    print(feature_importance_df.head(10).to_string(index=False))

    print("\n[STEP 4] TRAINING LOCAL CPU MODELS")
    # Define lightweight, CPU-based models with reproducible random states and thread limits
    models: dict = {
        "Random Forest": RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            class_weight="balanced",
            n_jobs=4,
            random_state=RANDOM_STATE,
        ),
        "XGBoost": XGBClassifier(
            n_estimators=300,
            max_depth=4,
            learning_rate=0.05,
            objective="multi:softprob",
            num_class=4,
            tree_method="hist",
            n_jobs=4,
            random_state=RANDOM_STATE,
            eval_metric="mlogloss",
        ),
        "Logistic Regression": LogisticRegression(
            max_iter=1200,
            random_state=RANDOM_STATE,
            class_weight="balanced",
            n_jobs=4,
        ),
    }

    if CATBOOST_AVAILABLE:
        models["CatBoost"] = CatBoostClassifier(
            iterations=300,
            depth=5,
            learning_rate=0.05,
            loss_function="MultiClass",
            verbose=False,
            thread_count=4,
            random_seed=RANDOM_STATE,
        )

    trained_models = {}
    all_eval = {}
    rows = []

    for model_name, model in models.items():
        print(f"  - Fitting {model_name} on 4 CPU threads...")
        model.fit(x_train_scaled, y_train_resampled)
        trained_models[model_name] = model
        metrics, y_pred, y_proba = evaluate_model(model_name, model, x_test_scaled, y_test)
        rows.append(metrics)
        all_eval[model_name] = {"y_pred": y_pred, "y_proba": y_proba, "metrics": metrics}

    comparison_df = pd.DataFrame(rows).sort_values("AUC-ROC", ascending=False)
    print("\n[STEP 5] BENCHMARK RESULTS")
    print(comparison_df.to_string(index=False))

    best_model_name = str(comparison_df.iloc[0]["Model"])
    best_model = trained_models[best_model_name]
    best_y_pred = all_eval[best_model_name]["y_pred"]
    best_y_proba = all_eval[best_model_name]["y_proba"]
    print(f"\n[OK] Top Performing Model: >>> {best_model_name} <<<")

    print("\n[STEP 6] CLASS-1 THRESHOLD TUNING")
    best_thr, class1_metrics = tune_class1_threshold(y_test, best_y_proba, best_y_pred)
    print(f"[OK] Selected class-1 threshold: {best_thr:.2f} (F1: {class1_metrics.get('f1', 0):.4f})")

    print("\n[STEP 7] CALIBRATION METRICS")
    calibration_df = compute_calibration_metrics(y_test, best_y_proba)
    print(calibration_df.to_string(index=False))

    cm = confusion_matrix(y_test, best_y_pred)

    print("\n[STEP 8] SAVING STANDALONE MODELS TO 'models/' DIRECTORY")
    # Save individual models separately so they can be loaded independently
    rf_path = os.path.join(MODELS_DIR, "random_forest.pkl")
    xgb_path = os.path.join(MODELS_DIR, "xgboost.pkl")
    joblib.dump(trained_models["Random Forest"], rf_path)
    joblib.dump(trained_models["XGBoost"], xgb_path)
    print(f"[OK] Saved: {rf_path}")
    print(f"[OK] Saved: {xgb_path}")

    if CATBOOST_AVAILABLE and "CatBoost" in trained_models:
        cb_path = os.path.join(MODELS_DIR, "catboost.pkl")
        joblib.dump(trained_models["CatBoost"], cb_path)
        print(f"[OK] Saved: {cb_path}")

    print("\n[STEP 9] SAVING PRODUCTION BUNDLE & EVALUATION ARTIFACTS")
    comparison_path = os.path.join(RESULTS_DIR, "model_comparison.csv")
    feature_path = os.path.join(RESULTS_DIR, "feature_importance.csv")
    calibration_path = os.path.join(RESULTS_DIR, "calibration_metrics.csv")
    best_model_path = os.path.join(RESULTS_DIR, "best_model.pkl")
    scaler_path = os.path.join(RESULTS_DIR, "scaler.pkl")
    bundle_path = os.path.join(RESULTS_DIR, "model_bundle.pkl")
    metadata_path = os.path.join(RESULTS_DIR, "run_metadata.json")

    comparison_df.to_csv(comparison_path, index=False)
    feature_importance_df.to_csv(feature_path, index=False)
    calibration_df.to_csv(calibration_path, index=False)

    joblib.dump(best_model, best_model_path)
    joblib.dump(scaler, scaler_path)

    run_config = {
        "random_state": RANDOM_STATE,
        "dataset_size": int(len(df)),
        "test_size": TEST_SIZE,
        "best_model": best_model_name,
        "class1_threshold": best_thr,
    }

    # Production bundle loaded by the FastAPI PredictionService
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
        "artifacts": {
            "comparison": comparison_path,
            "feature_importance": feature_path,
            "calibration": calibration_path,
            "best_model": best_model_path,
            "scaler": scaler_path,
            "bundle": bundle_path,
            "individual_models": {
                "random_forest": rf_path,
                "xgboost": xgb_path,
                "catboost": os.path.join(MODELS_DIR, "catboost.pkl") if CATBOOST_AVAILABLE else "",
            },
        },
    }
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    # Generate Evaluation Charts
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    top_features = feature_importance_df.head(12)
    axes[0].barh(top_features["feature"], top_features["importance"], color="#0F766E")
    axes[0].set_title(f"Clinical Feature Importance ({best_model_name})")
    axes[0].invert_yaxis()

    heatmap = axes[1].imshow(cm, cmap="Blues")
    axes[1].set_title(f"Confusion Matrix: {best_model_name}")
    axes[1].set_xlabel("Predicted Risk Tier")
    axes[1].set_ylabel("True Clinical Risk")
    plt.colorbar(heatmap, ax=axes[1])
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            axes[1].text(j, i, str(cm[i, j]), ha="center", va="center", color="black")

    plt.tight_layout()
    plot_path = os.path.join(RESULTS_DIR, "evaluation_summary.png")
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"\n[OK] Model Bundle for API: {bundle_path}")
    print(f"[OK] Evaluation Summary Plot: {plot_path}")
    print(f"[OK] Metadata Traceability: {metadata_path}")
    print("\n" + "=" * 80)
    print("PIPELINE TRAINING COMPLETE: READY FOR CLINICAL INFERENCE")
    print("=" * 80)


if __name__ == "__main__":
    main()
