# CKD-CI Results Summary (Standalone Runtime)

Generated on: 2026-03-28

## 1. Run Artifacts Reviewed
- Full pipeline metrics: [results/model_comparison.csv](results/model_comparison.csv)
- Advanced pipeline metrics: [results/advanced_models/model_comparison_advanced.csv](results/advanced_models/model_comparison_advanced.csv)
- Feature importance: [results/feature_importance.csv](results/feature_importance.csv)
- Full pipeline visualization: [results/evaluation_summary.png](results/evaluation_summary.png)
- Advanced pipeline visualization: [results/advanced_models/advanced_summary.png](results/advanced_models/advanced_summary.png)

## 2. Model Comparison Snapshot

### Full Pipeline (n=2000)
| Model | Accuracy | AUC-ROC | F1 (Weighted) |
|---|---:|---:|---:|
| Logistic Regression | 0.6775 | 0.8948 | 0.6771 |
| SVM | 0.6325 | 0.8731 | 0.6309 |
| Random Forest | 0.5950 | 0.8671 | 0.5904 |
| XGBoost | 0.5975 | 0.8645 | 0.5990 |

### Advanced Pipeline (n=1500)
| Model | Accuracy | AUC-ROC | F1 (Weighted) |
|---|---:|---:|---:|
| Logistic Regression | 0.6300 | 0.8775 | 0.6289 |
| SVM (RBF) | 0.6167 | 0.8549 | 0.6157 |
| Random Forest | 0.6100 | 0.8488 | 0.6077 |
| Extra Trees | 0.5867 | 0.8404 | 0.5784 |
| XGBoost | 0.5800 | 0.8348 | 0.5794 |
| HistGradientBoost | 0.5833 | 0.8347 | 0.5785 |
| MLP | 0.5667 | 0.8119 | 0.5676 |

## 3. Selected Candidate Model
**Primary candidate: Logistic Regression**

Why:
- Highest AUC in both full and advanced runs.
- Highest or near-highest weighted F1.
- Most stable behavior across both pipelines.
- Easiest to interpret clinically among tested models.

## 4. Diagnostic Notes From Plots
- Feature importance is clinically plausible: eGFR, BUN, age, hemoglobin, and creatinine dominate.
- Confusion matrices show strongest performance at classes 0 and 3.
- Main weakness is class 1 recall (low-risk class), with confusion into classes 0 and 2.

## 5. Top Features (Full Pipeline)
1. eGFR
2. bun
3. age
4. hemoglobin
5. creatinine
6. albumin
7. phosphate
8. education_years
9. systolic_bp
10. bmi

## 6. Recommended Next Actions
1. Improve class-1 recall using threshold tuning or class-weighted training.
2. Add calibration analysis (Brier score / reliability curve) for risk probability quality.
3. Validate with external or real clinical cohorts before deployment decisions.
4. Freeze model + preprocessing versions and create a small inference script for reproducible predictions.

## 7. Reproducible Commands
```powershell
Set-Location "C:\Users\hp\OneDrive\Documents\Downloads\CKD-CI (2)\CKD-CI"
.\run_all.bat
.\.venv312\Scripts\python.exe run_advanced_models.py
```
