import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
from sklearn.metrics import roc_curve, auc

np.random.seed(42)

print("=" * 70)
print("GENERATING ALL GRAPHS AND STATISTICS FOR YOUR PAPER")
print("=" * 70)

# =====================================================
# STEP 1: Create Synthetic Dataset
# =====================================================

print("\n📊 STEP 1: Creating dataset...")

n = 2378

data = pd.DataFrame({
    "age": np.random.normal(65, 10, n),
    "education_years": np.random.normal(12, 3, n),
    "eGFR": np.random.normal(70, 20, n),
    "creatinine": np.random.normal(1.0, 0.3, n),
    "bun": np.random.normal(18, 8, n),
    "gender": np.random.choice([0, 1], size=n)  # 0 = female, 1 = male
})

# Create KDI
data["KDI"] = (
    0.002 * data["age"] +
    -0.005 * data["education_years"] +
    -0.003 * data["eGFR"] +
    0.2 * data["creatinine"] +
    0.001 * data["bun"] +
    np.random.normal(0, 0.02, n)
)

# Logistic probability
logit = -3 + 8 * data["KDI"]
prob = 1 / (1 + np.exp(-logit))
data["cognitive_impairment"] = np.random.binomial(1, prob)

print(f"✅ Created dataset with {n} patients")
print(f"   Cognitive impairment: {data['cognitive_impairment'].sum()} patients ({data['cognitive_impairment'].mean()*100:.1f}%)")

# =====================================================
# STEP 2: TABLE 1 - Participant Characteristics
# =====================================================

print("\n📊 STEP 2: Creating TABLE 1 - Participant Characteristics...")

group0 = data[data["cognitive_impairment"] == 0]
group1 = data[data["cognitive_impairment"] == 1]

variables = ["age", "education_years", "eGFR", "creatinine", "bun", "KDI"]

rows = []

for var in variables:
    mean0, std0 = group0[var].mean(), group0[var].std()
    mean1, std1 = group1[var].mean(), group1[var].std()

    t, p = stats.ttest_ind(group0[var], group1[var])

    rows.append([
        var,
        f"{mean0:.2f} ± {std0:.2f}",
        f"{mean1:.2f} ± {std1:.2f}",
        f"{p:.4f}"
    ])

# Gender percentage
male0 = group0["gender"].mean() * 100
male1 = group1["gender"].mean() * 100
chi2, p_gender, _, _ = stats.chi2_contingency(
    pd.crosstab(data["gender"], data["cognitive_impairment"])
)

rows.append([
    "gender (% male)",
    f"{male0:.1f}%",
    f"{male1:.1f}%",
    f"{p_gender:.4f}"
])

table1 = pd.DataFrame(rows, columns=[
    "Characteristic",
    "Without Impairment",
    "With Impairment",
    "P-value"
])

print("\n📋 TABLE 1 - Participant Characteristics:")
print(table1)

# =====================================================
# STEP 3: TABLE 2 - Logistic Regression
# =====================================================

print("\n📊 STEP 3: Creating TABLE 2 - KDI Regression Results...")

X1 = sm.add_constant(data["KDI"])
model1 = sm.Logit(data["cognitive_impairment"], X1).fit(disp=False)

or1 = np.exp(model1.params.iloc[1])
ci1 = np.exp(model1.conf_int().iloc[1])
ci1_low, ci1_high = ci1[0], ci1[1]

X2 = sm.add_constant(data[["KDI", "age", "education_years"]])
model2 = sm.Logit(data["cognitive_impairment"], X2).fit(disp=False)

or2 = np.exp(model2.params.iloc[1])
ci2 = np.exp(model2.conf_int().iloc[1])
ci2_low, ci2_high = ci2[0], ci2[1]

table2 = pd.DataFrame({
    "Model": ["Unadjusted", "Adjusted"],
    "Odds Ratio (KDI)": [f"{or1:.2f}", f"{or2:.2f}"],
    "95% CI": [
        f"{ci1_low:.2f} - {ci1_high:.2f}",
        f"{ci2_low:.2f} - {ci2_high:.2f}"
    ]
})

print("\n📋 TABLE 2 - Logistic Regression Results:")
print(table2)

# =====================================================
# STEP 4: ROC Curve
# =====================================================

print("\n📊 STEP 4: Creating ROC Curve...")

fpr, tpr, _ = roc_curve(data["cognitive_impairment"], model1.predict(X1))
roc_auc = auc(fpr, tpr)

plt.figure()
plt.plot(fpr, tpr)
plt.plot([0, 1], [0, 1])
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title(f"ROC Curve (AUC = {roc_auc:.2f})")
plt.savefig("roc_curve.png")
plt.close()

print(f"✅ ROC Curve saved (AUC = {roc_auc:.3f})")

# =====================================================
# STEP 5: KDI Distribution Plot
# =====================================================

print("\n📊 STEP 5: Creating KDI Distribution Plot...")

plt.figure()
sns.histplot(group0["KDI"], kde=True, stat="density")
sns.histplot(group1["KDI"], kde=True, stat="density")
plt.xlabel("KDI")
plt.title("KDI Distribution by Cognitive Status")
plt.legend(["Without Impairment", "With Impairment"])
plt.savefig("kdi_distribution.png")
plt.close()

print("✅ KDI Distribution plot saved")

print("\n🎉 ALL TABLES AND GRAPHS GENERATED SUCCESSFULLY!")
print("=" * 70)