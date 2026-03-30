# ==========================================================
# ADVANCED STATISTICAL ANALYSIS - CKD & Cognitive Impairment
# College + Research + Journal Grade Implementation
# ==========================================================

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.metrics import roc_curve, auc, confusion_matrix
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.model_selection import KFold
from sklearn.linear_model import LogisticRegression

np.random.seed(42)

print("="*70)
print("ADVANCED STATISTICAL ANALYSIS PIPELINE")
print("="*70)

# ==========================================================
# 1️⃣ DATA GENERATION (Replace with real data if available)
# ==========================================================

n = 2378

data = pd.DataFrame({
    "age": np.random.normal(65, 10, n),
    "education_years": np.random.normal(12, 3, n),
    "eGFR": np.random.normal(70, 20, n),
    "creatinine": np.random.normal(1.0, 0.3, n),
    "bun": np.random.normal(18, 8, n),
    "gender": np.random.choice([0, 1], size=n)
})

data["KDI"] = (
    0.002 * data["age"]
    - 0.005 * data["education_years"]
    - 0.003 * data["eGFR"]
    + 0.2 * data["creatinine"]
    + 0.001 * data["bun"]
    + np.random.normal(0, 0.02, n)
)

logit = -3 + 8 * data["KDI"]
prob = 1 / (1 + np.exp(-logit))
data["cognitive_impairment"] = np.random.binomial(1, prob)

print(f"\nDataset created with {n} patients")

# ==========================================================
# 2️⃣ DESCRIPTIVE STATISTICS
# ==========================================================

print("\n📊 DESCRIPTIVE STATISTICS")

desc = data.groupby("cognitive_impairment").mean()
print(desc)

# ==========================================================
# 3️⃣ MULTIVARIABLE LOGISTIC REGRESSION
# ==========================================================

print("\n📊 MULTIVARIABLE LOGISTIC REGRESSION")

X = data[["KDI", "age", "education_years", "eGFR"]]
X = sm.add_constant(X)
y = data["cognitive_impairment"]

model = sm.Logit(y, X).fit(disp=False)

print(model.summary())

# Odds Ratios
or_values = np.exp(model.params)
ci = np.exp(model.conf_int())

results_table = pd.DataFrame({
    "Odds Ratio": or_values,
    "CI Lower": ci[0],
    "CI Upper": ci[1],
    "P-value": model.pvalues
})

print("\n📋 Odds Ratios with 95% CI")
print(results_table)

results_table.to_csv("advanced_logistic_results.csv")

# ==========================================================
# 4️⃣ MULTICOLLINEARITY CHECK (VIF)
# ==========================================================

print("\n📊 MULTICOLLINEARITY CHECK (VIF)")

vif_data = pd.DataFrame()
vif_data["Variable"] = X.columns
vif_data["VIF"] = [
    variance_inflation_factor(X.values, i)
    for i in range(X.shape[1])
]

print(vif_data)
vif_data.to_csv("vif_results.csv", index=False)

# ==========================================================
# 5️⃣ ROC & AUC
# ==========================================================

print("\n📊 ROC ANALYSIS")

pred_probs = model.predict(X)

fpr, tpr, _ = roc_curve(y, pred_probs)
roc_auc = auc(fpr, tpr)

plt.figure()
plt.plot(fpr, tpr)
plt.plot([0,1],[0,1])
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title(f"ROC Curve (AUC = {roc_auc:.3f})")
plt.savefig("advanced_roc_curve.png")
plt.close()

print(f"AUC = {roc_auc:.3f}")

# ==========================================================
# 6️⃣ CONFUSION MATRIX
# ==========================================================

print("\n📊 CONFUSION MATRIX")

y_pred = (pred_probs > 0.5).astype(int)
cm = confusion_matrix(y, y_pred)

tn, fp, fn, tp = cm.ravel()

sensitivity = tp / (tp + fn)
specificity = tn / (tn + fp)

print("Confusion Matrix:")
print(cm)
print(f"Sensitivity: {sensitivity:.3f}")
print(f"Specificity: {specificity:.3f}")

# ==========================================================
# 7️⃣ 5-FOLD CROSS VALIDATION
# ==========================================================

print("\n📊 5-FOLD CROSS VALIDATION")

kf = KFold(n_splits=5, shuffle=True, random_state=42)
auc_scores = []

X_ml = data[["KDI", "age", "education_years", "eGFR"]]
y_ml = data["cognitive_impairment"]

for train_index, test_index in kf.split(X_ml):
    X_train, X_test = X_ml.iloc[train_index], X_ml.iloc[test_index]
    y_train, y_test = y_ml.iloc[train_index], y_ml.iloc[test_index]

    model_cv = LogisticRegression(max_iter=1000)
    model_cv.fit(X_train, y_train)
    probs = model_cv.predict_proba(X_test)[:,1]

    fpr_cv, tpr_cv, _ = roc_curve(y_test, probs)
    auc_scores.append(auc(fpr_cv, tpr_cv))

print(f"Cross-validated AUC: {np.mean(auc_scores):.3f}")

print("\n🎉 ADVANCED STATISTICAL ANALYSIS COMPLETED")
print("="*70)