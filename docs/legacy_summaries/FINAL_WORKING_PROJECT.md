# CKD-CI Final Working Project Handoff

Generated on: 2026-03-28

## Project Status
This workspace now runs end-to-end with standalone scripts and verified outputs.

## Main Run Commands
From project folder:
```powershell
Set-Location "C:\Users\hp\OneDrive\Documents\Downloads\CKD-CI (2)\CKD-CI"
.\run_menu.ps1 -Mode all
```

From workspace root:
```powershell
Set-Location "C:\Users\hp\OneDrive\Documents\Downloads\CKD-CI (2)"
.\run_project.bat
```

Dashboard from workspace root:
```powershell
Set-Location "C:\Users\hp\OneDrive\Documents\Downloads\CKD-CI (2)"
.\run_project.bat dashboard
```

API from workspace root:
```powershell
Set-Location "C:\Users\hp\OneDrive\Documents\Downloads\CKD-CI (2)"
.\run_api.bat
```

## Individual Modes
```powershell
.\run_menu.ps1 -Mode quick
.\run_menu.ps1 -Mode full
.\run_menu.ps1 -Mode advanced
.\run_menu.ps1 -Mode dashboard
.\run_menu.ps1 -Mode api
.\run_menu.ps1 -Mode all
```

Dashboard from workspace root:
```powershell
Set-Location "C:\Users\hp\OneDrive\Documents\Downloads\CKD-CI (2)"
.\run_dashboard.bat
```

## Inference (Single/Multi-Patient CSV)
```powershell
.\.venv312\Scripts\python.exe infer_single_patient.py --input sample_patient.csv
```
Output file:
- `results/predictions.csv`

## Verified Output Files
- `results/model_comparison.csv`
- `results/feature_importance.csv`
- `results/best_model.pkl`
- `results/scaler.pkl`
- `results/evaluation_summary.png`
- `results/advanced_models/model_comparison_advanced.csv`
- `results/advanced_models/confusion_matrix_advanced.csv`
- `results/advanced_models/advanced_summary.png`
- `results/FINAL_RESULTS_SUMMARY.md`
- `results/calibration_metrics.csv`
- `results/model_bundle.pkl`
- `results/run_metadata.json`
- `requirements-runtime.txt`

## Real-World Readiness Additions
- Input schema and range guardrails in CLI/API/dashboard
- Class-1 threshold tuning stored in model bundle metadata
- Calibration reporting via Brier score per class
- Optional external dataset validation and drift report (`--external-data`)
- FastAPI service: `api_server.py`
- Automated tests: `tests/`
- Containerization: `Dockerfile`, `.dockerignore`
- CI pipeline: `.github/workflows/ci.yml`

## Useful Commands
Train with optional external dataset for drift checks:
```powershell
.\.venv312\Scripts\python.exe run_complete_pipeline.py --external-data your_external_data.csv
```

Run tests:
```powershell
.\.venv312\Scripts\python.exe -m pytest -q
```

Run API directly:
```powershell
.\.venv312\Scripts\python.exe -m uvicorn api_server:app --host 0.0.0.0 --port 8000
```

## Recommended Candidate Model
- Logistic Regression (best consistency across full + advanced runs)

## Notes
- This runtime is intentionally standalone and does not depend on missing legacy folders like `data/` and `src/`.
- Python environment used: `.venv312` (Python 3.12)
