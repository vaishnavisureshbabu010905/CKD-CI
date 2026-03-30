"""
Standalone advanced-model CKD-CI pipeline.

This script is independent of missing data/src modules and trains a broader
set of ML models with a consistent evaluation pipeline.
"""

import os
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

RANDOM_STATE = 42
DATASET_SIZE = 1500
TEST_SIZE = 0.2
RESULTS_DIR = os.path.join("results", "advanced_models")


def generate_synthetic_ckd_dataset(n_samples: int = 1500, random_state: int = 42) -> pd.DataFrame:
    """Generate synthetic CKD clinical data with balanced 4-class cognitive risk labels."""
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


def evaluate_model(model_name: str, model, x_test: np.ndarray, y_test: pd.Series) -> dict:
    """Evaluate multiclass classifier with weighted metrics and OVR AUC."""
    y_pred = model.predict(x_test)
    if hasattr(model, "predict_proba"):
        y_proba = model.predict_proba(x_test)
        auc_roc = roc_auc_score(y_test, y_proba, multi_class="ovr")
    else:
        auc_roc = float("nan")

    return {
        "Model": model_name,
        "Accuracy": accuracy_score(y_test, y_pred),
        "AUC-ROC": auc_roc,
        "Precision (Weighted)": precision_score(y_test, y_pred, average="weighted", zero_division=0),
        "Recall (Weighted)": recall_score(y_test, y_pred, average="weighted", zero_division=0),
        "F1-Score (Weighted)": f1_score(y_test, y_pred, average="weighted", zero_division=0),
    }


def main() -> tuple[dict, pd.DataFrame]:
    np.random.seed(RANDOM_STATE)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    print("\n" + "=" * 76)
    print("ADVANCED ML MODELS - STANDALONE CKD-CI PIPELINE")
    print("=" * 76)

    print("\n[STEP 1] DATA GENERATION")
    df = generate_synthetic_ckd_dataset(n_samples=DATASET_SIZE, random_state=RANDOM_STATE)
    print(f"[OK] Dataset shape: {df.shape}")
    print(f"[OK] Class distribution: {df['cognitive_risk'].value_counts().sort_index().to_dict()}")

    print("\n[STEP 2] PREPROCESSING")
    x = df.drop(columns=["cognitive_risk", "CKD_stage"])
    y = df["cognitive_risk"]
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

    print("\n[STEP 3] TRAINING ADVANCED MODEL SET")
    models = {
        "Logistic Regression": LogisticRegression(max_iter=1200, random_state=RANDOM_STATE),
        "Random Forest": RandomForestClassifier(n_estimators=260, max_depth=16, random_state=RANDOM_STATE, n_jobs=-1),
        "XGBoost": XGBClassifier(
            n_estimators=260,
            max_depth=6,
            learning_rate=0.06,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=RANDOM_STATE,
            eval_metric="mlogloss",
        ),
        "SVM (RBF)": SVC(kernel="rbf", probability=True, random_state=RANDOM_STATE),
        "Extra Trees": ExtraTreesClassifier(n_estimators=300, random_state=RANDOM_STATE, n_jobs=-1),
        "HistGradientBoost": HistGradientBoostingClassifier(max_depth=8, learning_rate=0.06, random_state=RANDOM_STATE),
        "MLP": MLPClassifier(hidden_layer_sizes=(128, 64), activation="relu", max_iter=300, random_state=RANDOM_STATE),
    }

    trained_models: dict = {}
    results = []

    for model_name, model in models.items():
        print(f"  - Training {model_name}...")
        model.fit(x_train_scaled, y_train_resampled)
        trained_models[model_name] = model
        results.append(evaluate_model(model_name, model, x_test_scaled, y_test))

    comparison_df = pd.DataFrame(results).sort_values("AUC-ROC", ascending=False)

    print("\n[STEP 4] EVALUATION SUMMARY")
    print(comparison_df.to_string(index=False))

    best_model_name = comparison_df.iloc[0]["Model"]
    best_model = trained_models[best_model_name]

    y_best = best_model.predict(x_test_scaled)
    cm = confusion_matrix(y_test, y_best)

    comparison_path = os.path.join(RESULTS_DIR, "model_comparison_advanced.csv")
    cm_path = os.path.join(RESULTS_DIR, "confusion_matrix_advanced.csv")
    plot_path = os.path.join(RESULTS_DIR, "advanced_summary.png")

    comparison_df.to_csv(comparison_path, index=False)
    pd.DataFrame(cm).to_csv(cm_path, index=False)

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_title(f"Confusion Matrix - {best_model_name}")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    plt.colorbar(im, ax=ax)

    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", color="black")

    plt.tight_layout()
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    print("\n[STEP 5] ARTIFACTS")
    print(f"[OK] Saved comparison: {comparison_path}")
    print(f"[OK] Saved confusion matrix: {cm_path}")
    print(f"[OK] Saved plot: {plot_path}")

    print("\n" + "=" * 76)
    print("ADVANCED PIPELINE STATUS: COMPLETE")
    print(f"BEST MODEL: {best_model_name}")
    print("=" * 76)

    return trained_models, comparison_df


if __name__ == "__main__":
    main()
