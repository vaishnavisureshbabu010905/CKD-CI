# CKD-CI — Chronic Kidney Disease Cognitive Impairment Clinical Decision Support Platform

![System Status](https://img.shields.io/badge/System%20Status-Operational-brightgreen)
![FastAPI Backend](https://img.shields.io/badge/FastAPI-v0.100+-blue)
![Next.js Frontend](https://img.shields.io/badge/Next.js-v14%20App%20Router-black)
![ML Models](https://img.shields.io/badge/Models-CatBoost%20%7C%20XGBoost%20%7C%20RF%20%7C%20LogReg-orange)
![Execution](https://img.shields.io/badge/Execution-100%25%20Local%20CPU-teal)
![Regulatory](https://img.shields.io/badge/Guidance-FDA%20SaMD%20%7C%20KDIGO%202024-purple)

**CKD-CI** is an enterprise-grade Clinical Decision Support (CDS) platform designed for nephrologists, neurologists, and healthcare teams to detect, stratify, and monitor **cognitive impairment risk in Chronic Kidney Disease (CKD) patients** using 18 routinely collected clinical and biochemical biomarkers.

Built with a **FastAPI** Python backend, local multi-threaded CPU machine learning models (**CatBoost, XGBoost, Random Forest, Platt-Calibrated Logistic Regression**), and a **Next.js 14 + Tailwind CSS** clinical SaaS frontend.

---

## Key Clinical & Architectural Features

### 1. Clinical Intelligence & Prediction Studio (`/prediction`)
- **18 Canonical Biomarkers**: Evaluates age, biological sex, formal education, comorbidities (diabetes, hypertension, CVD), renal panel (`eGFR`, `creatinine`, `BUN`, `UACR`), and metabolic/electrolyte markers (`hemoglobin`, `albumin`, `hsCRP`, `potassium`, `phosphate`, `calcium`, `systolic BP`, `BMI`).
- **Patient Data Isolation**: Selecting an enrolled patient loads **only** their verified records; unmeasured fields are highlighted with an amber border as *"Not on Record — Required"* to prevent default value bleed-through.
- **Calibrated Probabilities**: Standardized feature inputs (`StandardScaler`) coupled with Platt scaling output true per-class probabilities summing to 100% across 4 clinical risk tiers:
  - *No Cognitive Risk*
  - *Low Cognitive Risk*
  - *Moderate Cognitive Risk*
  - *High Cognitive Risk*
- **Explainable AI (XAI)**: Highlights primary driving variables (e.g., clearance reduction, microvascular barrier damage, systemic inflammation) alongside recommended care actions.

---

### 2. Clinical Workflow Decoupling (3 Separate Workflows)
To mirror real-world hospital operations, clinical information is strictly divided into three distinct lifecycles:
1. **Patient Registration (Collected Once)**:
   - **Patient Profile**: MRN, Full Name, Date of Birth (derives exact age), Biological Sex, Education Level (mapped to completed schooling years).
   - **Medical History**: Detailed comorbidity tracking including Diabetes (Type 1/2, duration in years), Hypertension (duration), Cardiovascular Disease (CAD, stroke, heart failure conditions), and CKD History (known stage G1–G5, duration, dialysis status).
2. **Clinical Encounters (Every Visit)**:
   - Separate modal to log routine hospital visits with updated lab telemetry (`eGFR`, `Creatinine`, `BUN`, `UACR`, `Systolic BP`, `BMI`, `Hgb`, `Albumin`, `hsCRP`).
   - Automatically updates current patient baseline and logs an audited encounter event to the longitudinal timeline.
3. **Cognitive Assessments (When Assessed)**:
   - Ground-truth neurocognitive screening log (`MoCA /30`, `MMSE /30`, `DSST`, `CERAD`, and clinical outcome impression).
   - **Target Leakage Safeguard**: Cognitive screening scores are kept strictly isolated from predictive ML model inputs to prevent target contamination.

---

### 3. Clinical Overview Command Center (`/command-center`)
- **Cohort Clinical Vulnerability Radar**: 6 real-time metrics showing clinical problems at scale across all patients:
  - *Severe Cognitive Risk* (Tier 3 patients)
  - *Moderate Impairment* (Surveillance needed)
  - *Stage G4–G5 Failure* (`eGFR < 30 mL/min`)
  - *Severe Albuminuria* (`UACR > 300 mg/g` / Stage A3)
  - *Diabetic Nephropathy Burden*
  - *Vascular Triad Exposure* (HTN / CAD / Stroke)
- **Cohort Clinical Problem Triage Queue**: Patient-by-patient table mapping identified clinical problems, telemetry, and actionable care protocols (e.g., *"Immediate MoCA & Nephrology Consult"*).
- **Live KDIGO 2024 Prognosis Grid**: Replaces static textbook tables with a **live cohort heatmap** mapping actual patients into their respective cells (`eGFR G1–G5 × UACR A1–A3`).

---

### 4. Patient Surveillance Suite
- **Critical Alerts (`/alerts`)**:
  - Real-time threshold surveillance for rapid eGFR loss (>5 mL/min/year) and acute albuminuria spikes.
  - Interactive status filtering: *All*, *Open/Urgent*, *Acknowledged*, *Resolved*.
  - Provider triage controls: One-click alert acknowledgment, resolution, and dispatching.
- **Longitudinal Trends (`/timeline`)**:
  - Trajectory monitoring across serial encounters (`eGFR`, `UACR`, `MoCA` score history).
  - Chronological event timeline displaying structured lab breakdowns and multi-class probability bars without raw object artifacts.
- **Model Governance & Registry (`/monitoring`)**:
  - Model registry table comparing all 4 trained CPU models evaluated under 5-fold cross-validation on NHANES clinical tabular data.
  - **Two-Sample Kolmogorov-Smirnov Feature Drift Test** tracking distribution stability across `eGFR`, `Creatinine`, `UACR`, and `Systolic BP`.
  - **FDA SaMD Governance Checklist** ensuring deterministic inference, local CPU guarantees, and auditability.

---

## Machine Learning Benchmark Comparison

Evaluated on $N = 2,500$ clinical tabular records using 5-fold cross-validation (CPU multi-threaded, seed 42):

| Model Architecture | Framework | Deployment Stage | Macro AUC-ROC | Macro F1 | Accuracy | Mean Brier Score | Log-Loss |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Platt-Calibrated Logistic Regression** | `scikit-learn` | **Active Production** | **89.61%** | **65.97%** | **70.0%** | **0.1023** | **0.6785** |
| **CatBoost Classifier** | `catboost` | Staging | **88.59%** | 62.32% | 65.6% | 0.1070 | 0.7163 |
| **XGBoost Classifier** | `xgboost` | Candidate | **88.31%** | 64.09% | 67.4% | 0.1103 | 0.7311 |
| **Random Forest** | `scikit-learn` | Baseline | **87.82%** | 63.74% | 68.2% | 0.1122 | 0.7802 |

> **CPU-Only Guarantee**: Models execute completely locally with zero GPU requirements, no external cloud dependencies, and zero outbound patient PHI transmission.

---

## Project Structure

```
CKD-CI/
├── api/                       # FastAPI REST API route handlers
│   └── routes/
│       ├── alerts.py          # Critical alert triage & dispatch
│       ├── auth.py            # JWT authentication & session tokens
│       ├── models.py          # Model registry, promotion & deprecation
│       ├── monitoring.py      # Data drift (KS-test) & metrics
│       ├── patients.py        # Patient profiles, visits & cognitive tests
│       ├── predictions.py     # AI inference endpoint
│       └── timeline.py        # Longitudinal surveillance timeline
├── config/                    # Application configuration & environment settings
├── core/                      # Security (bcrypt, JWT), logging & middleware
├── db/                        # SQLAlchemy database sessions & base models
├── frontend/                  # Next.js 14 App Router frontend
│   ├── app/
│   │   ├── alerts/            # Critical clinical alerts page
│   │   ├── command-center/    # Clinical Overview command center
│   │   ├── monitoring/        # Model governance & registry page
│   │   ├── patients/          # Patient directory & multi-step enrollment
│   │   │   └── [id]/          # Patient profile, visit & cognitive test modals
│   │   ├── prediction/        # Prediction Studio (18 biomarkers)
│   │   └── timeline/          # Longitudinal trends & trajectory page
│   ├── components/            # Clinical SaaS UI tokens & AppShell navigation
│   └── tailwind.config.ts     # Clinical navy (#16324F) & teal (#0F766E) palette
├── models/                    # SQLAlchemy database entity models
│   ├── alert.py
│   ├── model_registry.py
│   ├── patient.py             # Patient schema (features + medical_history)
│   ├── prediction.py
│   └── timeline.py            # Longitudinal surveillance events
├── results/                   # Trained models, metrics & scaler bundle
│   ├── model_bundle.pkl       # Production model bundle (scaler + model + labels)
│   └── model_comparison.csv   # 5-fold cross-validation benchmark matrix
├── services/                  # Business logic services
│   ├── demo_data.py           # Seed database with realistic clinical cohort
│   ├── model_loader.py        # Scaled inference service
│   └── prediction_service.py  # Probabilistic prediction engine
├── run_complete_pipeline.py   # Automated 4-model CPU training script
├── requirements.txt           # Python dependencies
└── ckdci.db                   # Local SQLite database
```

---

## Setup & Installation Guide

### Prerequisites
- **Python**: Version `3.10` or `3.11`
- **Node.js**: Version `18.x` or `20.x` (LTS)
- **OS**: Windows, macOS, or Linux

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/your-username/CKD-CI.git
cd CKD-CI
```

---

### Step 2: Set Up Backend Environment (Python)

1. **Create and activate a virtual environment**:
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv env
     .\env\Scripts\Activate.ps1
     ```
   - **Linux / macOS**:
     ```bash
     python3 -m venv env
     source env/bin/activate
     ```

2. **Install Python dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Verify Environment Variables (`.env`)**:
   Ensure `.env` exists in the project root with the following local configuration:
   ```ini
   APP_NAME="CKD-CI Clinical Decision Support"
   ENV="development"
   SECRET_KEY="super-secret-key-change-this-in-production"
   DATABASE_URL="sqlite:///./ckdci.db"
   MODEL_BUNDLE_PATH="results/model_bundle.pkl"
   LOG_LEVEL="INFO"
   ```

---

### Step 3: Train Machine Learning Models (Optional / Pre-bundled)
The repository includes pre-trained production model weights in `results/model_bundle.pkl`. To retrain the 4 CPU models (**Logistic Regression, CatBoost, XGBoost, Random Forest**) and generate fresh evaluation benchmarks:

```bash
python run_complete_pipeline.py --dataset-size 2500 --cv-folds 5
```
*Training completes in ~15–30 seconds on a standard 4-core CPU.*

---

### Step 4: Seed the Database
Seed the SQLite database with the default admin user and pre-populated clinical patient profiles:

- **Windows (PowerShell)**:
  ```powershell
  python -c "from db.base import Base; from db.session import engine, SessionLocal; from services.demo_data import ensure_demo_data; Base.metadata.create_all(bind=engine); db = SessionLocal(); ensure_demo_data(db); db.close(); print('Database seeded successfully!')"
  ```
- **Linux / macOS**:
  ```bash
  python3 -c "from db.base import Base; from db.session import engine, SessionLocal; from services.demo_data import ensure_demo_data; Base.metadata.create_all(bind=engine); db = SessionLocal(); ensure_demo_data(db); db.close(); print('Database seeded successfully!')"
  ```

---

### Step 5: Start the FastAPI Backend
Start the backend server on `http://127.0.0.1:8000`:

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **Health Check**: `http://127.0.0.1:8000/health`

---

### Step 6: Set Up Frontend (Next.js)

Open a **new terminal**:

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install Node dependencies**:
   ```bash
   npm install
   ```

3. **Verify TypeScript compilation**:
   ```bash
   npx tsc --noEmit
   ```

4. **Start the Next.js development server**:
   ```bash
   npm run dev
   ```
   The application dashboard will be available at: **`http://localhost:3000`**

---

## Default Clinical Credentials

| Role | Email | Password | Access Scope |
| :--- | :--- | :--- | :--- |
| **Nephrologist / Admin** | `admin@example.com` | `change_me` | Full clinical access, patient enrollment, inference, alert triage, model promotion |

---

## Clinical Safety & Disclaimer

> **IMPORTANT CLINICAL GOVERNANCE NOTICE**:
> 
> The **CKD-CI platform** is an investigational Clinical Decision Support (CDS) system intended to assist licensed healthcare providers in neurocognitive risk stratification. It is **not** an autonomous diagnostic device. 
> 
> All risk scores, probabilities, and protocol recommendations must be corroborated by formal neuropsychological evaluations (such as the Montreal Cognitive Assessment) and clinical nephrology judgment. Ground-truth cognitive scores are recorded separately to prevent algorithmic feedback loops and target leakage.
