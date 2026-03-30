"""
Ultra-fast CKD-CI test - quick verification (< 2 minutes)
No hyperparameter tuning, just model training and comparison
"""

import sys
import os
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')


def generate_synthetic_ckd_dataset(n_samples: int = 500, random_state: int = 42) -> pd.DataFrame:
    """Generate a realistic synthetic CKD cognitive-risk dataset for standalone runs."""
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
        egfr >= 90, 'G1',
        np.where(egfr >= 60, 'G2', np.where(egfr >= 45, 'G3a', np.where(egfr >= 30, 'G3b', np.where(egfr >= 15, 'G4', 'G5'))))
    )

    return pd.DataFrame({
        'age': age,
        'education_years': education_years,
        'gender': gender,
        'eGFR': egfr,
        'creatinine': creatinine,
        'bun': bun,
        'uacr': uacr,
        'hemoglobin': hemoglobin,
        'albumin': albumin,
        'hsCRP': hscrp,
        'potassium': potassium,
        'phosphate': phosphate,
        'calcium': calcium,
        'systolic_bp': systolic_bp,
        'bmi': bmi,
        'diabetes': diabetes,
        'hypertension': hypertension,
        'cvd': cvd,
        'CKD_stage': ckd_stage,
        'cognitive_risk': cognitive_risk
    })

print("\n" + "="*70)
print("CKD-CI QUICK TEST - Ultra-Fast Version")
print("="*70 + "\n")

# STEP 1: Data Generation
print("STEP 1: Generating synthetic CKD dataset (500 samples)...")
df = generate_synthetic_ckd_dataset(n_samples=500, random_state=42)
print(f"✓ Dataset generated: {df.shape}")
print(f"✓ Classes: {df['cognitive_risk'].value_counts().sort_index().to_dict()}")

# STEP 2: Preprocessing
print("\nSTEP 2: Data Preprocessing...")
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE

# Remove non-numeric columns
X = df.drop(columns=['cognitive_risk', 'CKD_stage'])
y = df['cognitive_risk']

# Handle missing values
X = X.fillna(X.mean())

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Apply SMOTE to handle class imbalance
smote = SMOTE(k_neighbors=3, random_state=42)
X_train_smote, y_train_smote = smote.fit_resample(X_train, y_train)

# Scale features
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train_smote)
X_test = scaler.transform(X_test)

print(f"✓ Training set: {X_train.shape}")
print(f"✓ Test set: {X_test.shape}")
print(f"✓ Features: {X.shape[1]}")

# STEP 3: Train Simple Models (No Grid Search)
print("\nSTEP 3: Training ML models (simple, no tuning)...")

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.svm import SVC

models = {}

# Logistic Regression
print("  • Logistic Regression...", end='', flush=True)
lr = LogisticRegression(max_iter=1000, random_state=42)
lr.fit(X_train, y_train_smote)
models['Logistic Regression'] = lr
print(" ✓")

# Random Forest (small)
print("  • Random Forest...", end='', flush=True)
rf = RandomForestClassifier(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train_smote)
models['Random Forest'] = rf
print(" ✓")

# XGBoost (small)
print("  • XGBoost...", end='', flush=True)
xgb = XGBClassifier(n_estimators=50, max_depth=5, learning_rate=0.1, random_state=42, eval_metric='mlogloss')
xgb.fit(X_train, y_train_smote)
models['XGBoost'] = xgb
print(" ✓")

# SVM (linear kernel - faster)
print("  • SVM...", end='', flush=True)
svm = SVC(kernel='linear', probability=True, random_state=42)
svm.fit(X_train, y_train_smote)
models['SVM'] = svm
print(" ✓")

# STEP 4: Evaluate
print("\nSTEP 4: Evaluating models...")
from sklearn.metrics import accuracy_score, roc_auc_score, f1_score, log_loss

results = []
for model_name, model in models.items():
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)
    
    metrics = {
        'Model': model_name,
        'Accuracy': accuracy_score(y_test, y_pred),
        'AUC-ROC': roc_auc_score(y_test, y_pred_proba, multi_class='ovr'),
        'F1-Score': f1_score(y_test, y_pred, average='weighted', zero_division=0),
        'Log Loss': log_loss(y_test, y_pred_proba)
    }
    results.append(metrics)

comparison_df = pd.DataFrame(results)

print("\n" + "="*70)
print("MODEL PERFORMANCE COMPARISON")
print("="*70)
print(comparison_df.to_string(index=False))

# STEP 5: Save Results
print("\nSTEP 5: Saving results...")
os.makedirs('results', exist_ok=True)
comparison_df.to_csv('results/model_comparison.csv', index=False)
print("✓ Results saved to results/model_comparison.csv")

# Find best model
best_idx = comparison_df['Accuracy'].idxmax()
best_model_name = comparison_df.iloc[best_idx]['Model']
best_accuracy = comparison_df.iloc[best_idx]['Accuracy']

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"✓ Best Model: {best_model_name}")
print(f"✓ Best Accuracy: {best_accuracy:.2%}")
print(f"✓ Results saved: results/model_comparison.csv")

print("\n" + "="*70)
print("QUICK TEST COMPLETE! ✓")
print("="*70)
print("\nNext steps:")
print("1. View results: more results/model_comparison.csv")
print("2. Run full pipeline: python run_complete_pipeline.py")
print("3. Launch dashboard: streamlit run deployment/dashboard.py")
print("="*70 + "\n")
