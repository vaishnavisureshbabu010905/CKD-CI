# CKD-CI: Master Interview Presentation & Deep-Dive Script

> **Project Title**: CKD-CI — Chronic Kidney Disease Cognitive Impairment Clinical Decision Support Platform  
> **Tech Stack**: FastAPI (Python 3.11), SQLAlchemy, SQLite, Scikit-Learn, CatBoost, XGBoost, Next.js 14 (App Router), TypeScript, Tailwind CSS  
> **Target Audience**: Technical Interviewers, HealthTech Hiring Managers, Data Science & Machine Learning Engineers

---

## Table of Contents
1. [Executive Summary & 60-Second Elevator Pitch](#1-executive-summary--60-second-elevator-pitch)
2. [Section 1: The Clinical Need & Project Objective](#section-1-the-clinical-need--project-objective)
3. [Section 2: Comprehensive Feature Overview](#section-2-comprehensive-feature-overview)
4. [Section 3: System Architecture & Data Flow](#section-3-system-architecture--data-flow)
5. [Section 4: File-by-File & Folder-by-Folder Technical Blueprint](#section-4-file-by-file--folder-by-folder-technical-blueprint)
6. [Section 5: Deep-Dive into Key Functions, Algorithms & Logic](#section-5-deep-dive-into-key-functions-algorithms--logic)
7. [Section 6: The Spoken Presentation Script (Step-by-Step Delivery)](#section-6-the-spoken-presentation-script-step-by-step-delivery)
8. [Section 7: Anticipated Interview Questions & Model Answers](#section-7-anticipated-interview-questions--model-answers)

---

## 1. Executive Summary & 60-Second Elevator Pitch

> *"Good morning / afternoon. Today, I am excited to present **CKD-CI**, an enterprise-grade Clinical Decision Support platform designed to predict and monitor cognitive impairment risk in Chronic Kidney Disease patients.*
> 
> *Cognitive impairment affects up to 60% of patients with advanced kidney disease due to shared vascular injury in the kidney-brain axis. Yet, it frequently goes undiagnosed until severe dementia develops because routine cognitive screening is time-consuming and specialists are scarce.*
> 
> *To solve this, I designed and engineered a full-stack, production-ready healthcare application. It leverages **18 routinely collected clinical and biochemical biomarkers** to perform 4-tier risk stratification using CPU-optimized machine learning models—achieving an **AUC-ROC of 89.61%** with Platt-calibrated probabilities.*
> 
> *Architecturally, the system decouples clinical workflows into **one-time patient registration**, **per-visit laboratory encounters**, and **independent neurocognitive assessments**—introducing a strict **target leakage safeguard**. The frontend is built on **Next.js 14 and TypeScript**, while the backend runs an asynchronous **FastAPI service with SQLite persistence**, live feature drift tracking, and FDA SaMD-aligned audit logging."*

---

## Section 1: The Clinical Need & Project Objective

### 1.1 The Clinical Problem (The Kidney-Brain Axis)
1. **High Prevalence & Hidden Onset**:
   - Cognitive impairment (CI) occurs in **30% to 60%** of patients with stage G3–G5 Chronic Kidney Disease (CKD), particularly targeting **executive function**, **processing speed**, and **working memory**.
   - Traditional nephrology appointments prioritize eGFR, fluid overload, and electrolyte balance; subtle cognitive decline is routinely overlooked until it impairs medication adherence, dialysis compliance, and quality of life.
2. **The Biological Analogy (Vascular Anatomical Homology)**:
   - The microvasculature of the **renal glomerulus** and the **cerebral periventricular white matter** share identical low-resistance, high-flow hemodynamic properties.
   - Chronic hypertension, diabetic microangiopathy, and uremic neurotoxins simultaneously damage glomerular podocytes (causing **albuminuria / UACR elevation**) and cerebral small vessels (causing **subcortical ischemic white matter injury**).
   - Therefore, kidney biomarkers directly reflect cerebral microvascular damage.
3. **The Diagnostic Bottleneck**:
   - Neuropsychological evaluations like the **Montreal Cognitive Assessment (MoCA)** or specialized MRI imaging require dedicated clinical time and specialist personnel that community clinics do not have.

### 1.2 The Project Objective
- **Primary Objective**: Build a deterministic, non-invasive, lightweight machine learning system that stratifies cognitive vulnerability using **standard, inexpensive laboratory and demographic markers** already captured in routine CKD consultations.
- **Secondary Objectives**:
  - **Zero-Cloud & Zero-GPU Footprint**: Ensure 100% offline, local CPU execution with zero patient Protected Health Information (PHI) transmission.
  - **Calibrated Multi-Class Output**: Move beyond simplistic binary classification to output true, calibrated risk probabilities across 4 tiers: *No Risk*, *Low Risk*, *Moderate Risk*, and *High Risk*.
  - **Actionable Decision Support**: Provide clinicians with clear explainability (primary biomarker drivers) and protocol actions (e.g., immediate MoCA trigger, SGLT2i optimization, nephrotoxicity review).

---

## Section 2: Comprehensive Feature Overview

### 2.1 The 18 Canonical Clinical Biomarkers
The system accepts 18 specific biological and demographic inputs validated against epidemiological datasets (NHANES):
1. **Demographics & Cognitive Reserve**: `age`, `gender` (0=F, 1=M), `education_years` (years of formal schooling; proxy for cognitive reserve).
2. **Clinical Comorbidity Flags**: `diabetes` (0/1), `hypertension` (0/1), `cvd` (cardiovascular disease, stroke, CAD, heart failure: 0/1).
3. **Renal Function Panel**:
   - `eGFR` (mL/min/1.73m²): Glomerular filtration rate via CKD-EPI equation.
   - `creatinine` (mg/dL): Muscle breakdown waste cleared by glomeruli.
   - `bun` (Blood Urea Nitrogen, mg/dL): Uremic solute accumulation.
   - `uacr` (Urine Albumin-to-Creatinine Ratio, mg/g): Glomerular barrier permeability damage.
4. **Metabolic & Electrolyte Panel**:
   - `hemoglobin` (g/dL): Renal anemia biomarker (reduces cerebral oxygen delivery).
   - `albumin` (g/dL): Serum albumin (nutritional status, systemic inflammation, frailty).
   - `hsCRP` (mg/L): High-sensitivity C-reactive protein (systemic microvascular inflammation).
   - `potassium` (mmol/L), `phosphate` (mg/dL), `calcium` (mg/dL): Mineral and bone metabolism markers.
   - `systolic_bp` (mmHg): Hemodynamic cerebral perfusion pressure.
   - `bmi` (kg/m²): Body Mass Index (metabolic syndrome marker).

---

### 2.2 Decoupled 3-Phase Clinical Workflows
A hallmark innovation of this platform is the separation of clinical data into three distinct operational lifecycles:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ WORKFLOW 1: PATIENT REGISTRATION (Collected Once at Intake)                  │
│ • Patient Profile: MRN, Full Name, Date of Birth (derives Age), Sex          │
│ • Education Level: Categorical selector auto-derives education_years         │
│ • Medical History: Detailed comorbidity tracking (Diabetes type & duration,  │
│   HTN duration, CVD specific conditions [CAD/Stroke/HF], CKD stage & dialysis│
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            ▼                                                     ▼
┌──────────────────────────────────────┐  ┌───────────────────────────────────┐
│ WORKFLOW 2: CLINICAL ENCOUNTERS      │  │ WORKFLOW 3: COGNITIVE ASSESSMENTS │
│ (Every Hospital Visit)               │  │ (When Assessed)                   │
│ • Logged per visit: SBP, BMI, eGFR,  │  │ • Recorded separately: MoCA score │
│   Cr, BUN, UACR, K, Phos, Ca, Hgb,   │  │   (/30), MMSE, DSST, CERAD, and   │
│   Albumin, hsCRP                     │  │   clinical impression.            │
│ • Updates current patient baseline   │  │ • ⚠️ Target Leakage Safeguard:    │
│ • Appends to longitudinal timeline   │  │   Strictly isolated from predictive│
│                                      │  │   features to avoid contamination!│
└──────────────────┬───────────────────┘  └───────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ WORKFLOW 4: PREDICTION STUDIO (Clinical Decision Support)                    │
│ • Auto-assembles: Profile Demographics + Medical History + Latest Visit Labs │
│ • Missing fields are highlighted in amber: "Not on Record — Required"        │
│ • Evaluates multi-class calibrated probabilities summing to 100%             │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

### 2.3 Dashboard Interfaces

#### A. Clinical Overview Command Center (`/command-center`)
- **Cohort Clinical Vulnerability Radar**: 6 high-level population metric cards showing total patients, severe cognitive risk count, moderate impairment requiring MoCA, stage G4–G5 renal failure, severe albuminuria (A3), and diabetic comorbidity.
- **Cohort Problem Triage Queue**: Live table of all patients displaying their specific clinical problem tags (e.g., *Critical Cognitive Risk*, *Stage A3 UACR*, *Severe eGFR Loss*), current labs, risk tier, and an actionable protocol recommendation (*"Immediate MoCA & Nephrology Consult"*).
- **Live KDIGO 2024 Cohort Map**: Replaces static textbook tables with a **populated cohort matrix** mapping real patients into grid cells (`eGFR G1–G5 × UACR A1–A3`).

#### B. Prediction Studio (`/prediction`)
- **Patient Data Isolation**: Selecting a registered patient populates *only* their verified parameters. Unmeasured parameters show as empty with an amber outline (`Not on Record — Required for Assessment`), disabling the compute button until all 18 features are confirmed.
- **Calibrated Probabilities**: Displays bar graphs for all 4 risk tiers summing to 100%.
- **Explainability**: Summarizes the dominant contributing drivers (e.g., reduced filtration, microvascular barrier breakdown, active systemic inflammation).
- **Persistence**: Predictions are saved to the database with a unique ID and logged to the patient's audit trail.

#### C. Patient Directory & Patient Detail Chart (`/patients` & `/patients/[id]`)
- **Multi-Step Enrollment Wizard**: 3-step intake (Identity -> Medical History -> Baseline Review).
- **Patient Detail Chart**: Clinical telemetry tiles, medical history comorbidity cards, **"Log Clinical Visit"** modal, **"Record Cognitive Test"** modal, and instant **PDF Clinical Report Export**.

#### D. Patient Surveillance Suite
- **Critical Alerts (`/alerts`)**: Real-time threshold violation cards with provider **Acknowledge** and **Resolve** action workflows, plus manual alert dispatching.
- **Longitudinal Trends (`/timeline`)**: Patient-specific trajectory monitoring with eGFR, UACR, and MoCA analytics, accompanied by structured payload viewers (clean probability cards without raw object artifacts).
- **Model Governance (`/monitoring`)**: Active production model card, 4-model cross-validation matrix, **Two-sample Kolmogorov-Smirnov (KS) feature drift detection**, and FDA SaMD compliance checklists.

---

## Section 3: System Architecture & Data Flow

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ NEXT.JS 14 FRONTEND (Client Layer)                                            │
│ React Server & Client Components • Tailwind CSS • Lucide Icons • Fetch API   │
│ Pages: /command-center, /patients, /prediction, /alerts, /timeline, /monitoring│
└──────────────────────────────────────┬────────────────────────────────────────┘
                                       │ HTTP / JSON (Bearer JWT)
                                       ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ FASTAPI APPLICATION (Gateway & Routing Layer)                                 │
│ SlowAPI Rate Limiter • Request ID Middleware • CORS • Auth Security (Passlib) │
│ Routers: /auth, /patients, /predictions, /alerts, /timeline, /models          │
└──────────────┬───────────────────────┬────────────────────────┬───────────────┘
               │                       │                        │
               ▼                       ▼                        ▼
┌─────────────────────────┐ ┌──────────────────────┐ ┌──────────────────────────┐
│ PERSISTENCE LAYER       │ │ PREDICTION ENGINE    │ │ GOVERNANCE & METRICS     │
│ SQLAlchemy ORM          │ │ StandardScaler       │ │ Kolmogorov-Smirnov Drift │
│ SQLite DB (ckdci.db)    │ │ Platt Calibrated     │ │ Audit Logging Stream     │
│ Entities: Patient,      │ │ Logistic Regression  │ │ Prometheus Metrics       │
│ Prediction, AlertEvent, │ │ (CatBoost / XGBoost  │ │ SaMD Compliance Engine   │
│ TimelineEvent, Registry │ │  / Random Forest)    │ │                          │
└─────────────────────────┘ └──────────────────────┘ └──────────────────────────┘
```

---

## Section 4: File-by-File & Folder-by-Folder Technical Blueprint

Here is the exact technical breakdown of the codebase:

### Root Directory
- **`run_complete_pipeline.py`**:
  - The standalone training engine. Synthesizes an $N=2,500$ clinical cohort using statistical correlations mirroring NHANES.
  - Implements **5-Fold Stratified Cross-Validation**.
  - Trains 4 models: **Logistic Regression** (L2 penalty, liblinear), **CatBoost** (hist-tree, multiclass), **XGBoost** (tree_method="hist", softprob), and **Random Forest** (balanced weights).
  - Evaluates Macro AUC-ROC, Macro F1, Accuracy, Log-Loss, and Brier Score.
  - Saves best model and scaler into `results/model_bundle.pkl` and individual weights into `models/`.
- **`main.py`**:
  - Entry point for FastAPI. Configures middleware (`RequestIDMiddleware`, `SlowAPIMiddleware`, `CORSMiddleware`).
  - Registers all API routers.
  - Handles startup bootstrapping via `startup_bootstrap()` to initialize DB tables and seed demo data.
- **`requirements.txt`**: Pins production dependencies (`fastapi`, `uvicorn`, `scikit-learn`, `catboost`, `xgboost`, `sqlalchemy`, `bcrypt==4.0.1`, `passlib`).
- **`.env`**: Configures database connection string (`sqlite:///./ckdci.db`), secret keys, and model artifact paths.

---

### Backend: `services/`
- **`services/model_loader.py`**:
  - `ModelLoader`: Singleton class that reads `results/model_bundle.pkl`.
  - **Critical Logic**: The `predict_proba(features)` method extracts the bundled `StandardScaler`, scales raw feature inputs with `scaler.transform(X)`, and runs `model.predict_proba(X_scaled)` to prevent probability collapse.
  - Resolves integer classes back to human labels (`{0: "No Cognitive Risk", 1: "Low Cognitive Risk", ...}`).
- **`services/prediction_service.py`**:
  - `PredictionService`: Orchestrates inference requests.
  - Validates feature vectors against `core/validation.py`.
  - Persists prediction results into the `predictions` table.
  - Logs an event into `timeline_events` with the probability payload.
  - Emits audit records via `log_audit()`.
- **`services/demo_data.py`**:
  - `ensure_demo_data(db)`: Populates empty databases with default users (`admin@example.com`), 3 demo patients (`CKD-1001 Amina Rahman`, `CKD-1002 David Okoro`, `CKD-1003 Sara Ibrahim`) with all 18 features and medical histories, tasks, alert events, and registers the 4 benchmark models in `model_registry`.

---

### Backend: `api/routes/`
- **`api/routes/patients.py`**:
  - `create_patient()`: Registers patient profile + medical history + optional baseline labs.
  - `get_patient()`: Fetches patient chart by ID.
  - `update_patient()` (`PUT /{id}`): Updates patient profile or features.
  - `record_clinical_visit()` (`POST /{id}/visits`): Logs encounter measurements (eGFR, Cr, BUN, UACR, BP, BMI) and appends encounter to clinical timeline.
  - `record_cognitive_assessment()` (`POST /{id}/cognitive-assessments`): Logs ground-truth MoCA/MMSE scores with explicit target leakage safeguard.
  - `patient_report_pdf()`: Generates dynamic PDF clinical report.
- **`api/routes/predictions.py`**:
  - `predict()`: Accepts single-patient features, calls `PredictionService`, returns predicted label, confidence, and calibrated class probabilities.
  - `history()`: Returns paginated historical predictions.
- **`api/routes/alerts.py`**:
  - `list_events()`: Retrieves surveillance alerts.
  - `acknowledge_event()` (`POST /{id}/ack`): Updates alert status to `acknowledged`.
  - `resolve_event()` (`POST /{id}/resolve`): Updates alert status to `resolved`.
  - `create_event()`: Clinician manual alert dispatch.
- **`api/routes/models.py`**:
  - `list_models()`: Returns registered models, frameworks, stages, and benchmark metrics.
  - `active_model()`: Returns the currently deployed production model.
  - `promote_model()`: Promotes staging model to active production.
- **`api/routes/timeline.py`**:
  - `get_timeline()`: Returns chronological surveillance history for a patient.
- **`api/routes/monitoring.py`**:
  - `drift()`: Computes two-sample KS-test drift score on eGFR distributions.
  - `summary()`: Exposes request counts, latency, and error metrics.

---

### Backend: `models/` (SQLAlchemy Entities)
- **`models/patient.py`**: Table `patients`. Stores `patient_identifier`, `first_name`, `last_name`, `date_of_birth`, `sex`, `medical_history` (JSON), and `features` (JSON).
- **`models/prediction.py`**: Table `predictions`. Stores input features, predicted label, confidence, probability distribution, model version, and user ID.
- **`models/timeline.py`**: Table `timeline_events`. Stores `source_type` (`clinical_visit`, `cognitive_assessment`, `prediction`, `alert`, `intake`), timestamp, summary, and JSON `payload`.
- **`models/alert.py`**: Tables `alert_rules` and `alert_events`.
- **`models/model_registry.py`**: Table `model_registry`. Tracks model names, versions, stages (`prod`, `staging`, `candidate`), paths, and metrics JSON.

---

### Frontend: `frontend/app/` (Next.js 14)
- **`app/command-center/page.tsx`**: Clinical Overview Command Center. Cohort Vulnerability Radar, Cohort Problem Triage Queue with protocol actions, and Live Cohort KDIGO Matrix.
- **`app/prediction/page.tsx`**: Prediction Studio. Guided intake across Demographics, Renal, and Metabolic tabs. Patient selection auto-fills verified values; missing fields are highlighted in amber. Multiclass probability bars.
- **`app/patients/page.tsx`**: Patient Cohort Directory with filter ribbon and **3-Step Patient Enrollment Wizard** (Profile -> Medical History -> Baseline Review).
- **`app/patients/[id]/page.tsx`**: Comprehensive Patient Detail Chart. Displays medical history cards, baseline lab tiles, **"Log Clinical Visit"** modal, **"Record Cognitive Assessment"** modal, and timeline stream.
- **`app/alerts/page.tsx`**: Critical Alerts & Escalation Center. Filter pills (All/Open/Ack/Resolved), Acknowledge and Resolve action buttons, and alert creation modal.
- **`app/timeline/page.tsx`**: Longitudinal Trends & Trajectory Surveillance. Trajectory summary cards (eGFR, UACR, MoCA), categorical filter pills, and structured payload breakdown (clean probability bars, no `[object Object]`).
- **`app/monitoring/page.tsx`**: Model Governance. Production model hero KPI cards, 4-model cross-validation comparison table, KS-test feature drift monitoring, and FDA SaMD compliance checklist.
- **`components/ui/`**: Clinical SaaS design system components (`button.tsx`, `card.tsx`, `badge.tsx`, `input.tsx`, `nav.tsx`, `spinner.tsx`, `error-banner.tsx`).
- **`tailwind.config.ts`**: Clinical color palette: Navy `#16324F`, Teal `#0F766E`, Risk Critical `#DC2626`, Risk Moderate `#EA580C`, Risk Normal `#059669`.

---

## Section 5: Deep-Dive into Key Functions, Algorithms & Logic

### 5.1 The Probability Calibration Bug & Its Solution
- **The Problem**: During initial testing, the model outputs showed ~99.9% probability for one class and 0.01% for all others.
- **The Diagnosis**: In `services/model_loader.py`, `model.predict_proba(X)` was being fed **unscaled raw feature values** (e.g., UACR of 380, eGFR of 42). Since Logistic Regression with L2 regularization is a linear model computed via $z = w^T x + b$, raw inputs of magnitude 300+ blew the logits into extreme saturation ($z \gg 10$), collapsing softmax to 1.0.
- **The Fix**: In `ModelLoader.predict_proba()`, we ensure the bundled `StandardScaler` transforms the vector:
  ```python
  X_scaled = self.scaler.transform(X)
  probabilities = self.model.predict_proba(X_scaled)[0]
  ```
  Now, logits remain centered, producing smooth, clinically calibrated probability distributions (e.g., *Moderate: 47.4%, High: 38.9%, Low: 13.6%, No Risk: 0.1%*).

---

### 5.2 Target Leakage Safeguard
- **What is Target Leakage?** If an ML model is trained to predict cognitive impairment based on clinical biomarkers, feeding MoCA/MMSE scores directly into the model as input features would represent target leakage—the model would trivially learn that a MoCA < 26 equals impairment, rendering biomarker predictions useless.
- **Architectural Safeguard**:
  - In `api/routes/patients.py`, the `record_cognitive_assessment()` endpoint saves MoCA and MMSE scores exclusively to the `timeline_events` table for clinician ground-truth tracking.
  - It **never** writes to `patient.features`.
  - In `frontend/app/prediction/page.tsx`, the model schema strictly excludes cognitive test scores, ensuring 100% predictive integrity.

---

### 5.3 Automated Patient Demographic Derivation
Rather than forcing clinicians to manually enter duplicate numbers:
1. `age` is calculated on-the-fly from `date_of_birth`:
   $$\text{Age} = \text{Current Year} - \text{DOB Year} - (\text{Day Passed Adjustment})$$
2. `gender` is automatically mapped from biological sex (`Female = 0`, `Male = 1`).
3. `education_years` is derived from standard education level categories:
   - *No formal schooling* $\to 0\text{ years}$
   - *Primary education* $\to 5\text{ years}$
   - *Secondary education* $\to 10\text{ years}$
   - *Higher secondary* $\to 12\text{ years}$
   - *Undergraduate / Graduate* $\to 16\text{ years}$
   - *Postgraduate or above* $\to 18\text{ years}$

---

### 5.4 Two-Sample Kolmogorov-Smirnov Feature Drift Test
In `monitoring/drift.py`:
- Real-time feature drift is monitored on continuous inputs (e.g., `eGFR`) using the non-parametric **Kolmogorov-Smirnov two-sample test**:
  $$D = \sup_x |F_{\text{baseline}}(x) - F_{\text{current}}(x)|$$
- If the maximum vertical deviation between cumulative distribution functions exceeds a threshold ($p < 0.05$ or $D > 0.3$), a drift alert is flagged in `/monitoring`, warning administrators that the patient population has shifted away from the training distribution.

---

## Section 6: The Spoken Presentation Script (Step-by-Step Delivery)

You can read or follow this script directly during your presentation:

---

### Slide 1: Introduction & Title
*"Good morning. My name is [Your Name], and today I am presenting **CKD-CI**, an AI-powered Clinical Decision Support platform designed to predict and monitor cognitive impairment in patients with Chronic Kidney Disease.*

*I developed this project to demonstrate how clinical machine learning research can be engineered into a full-stack, production-grade medical software application that adheres to clinical guidelines and software engineering best practices."*

---

### Slide 2: The Clinical Need & The Kidney-Brain Axis
*"Let’s start with the problem. Between 30% and 60% of patients with Chronic Kidney Disease suffer from cognitive impairment. This is not coincidental—the microvasculature of the kidney glomerulus and the deep white matter of the brain share identical anatomical properties. When hypertension, diabetes, and uremic toxins damage the kidney barrier, they simultaneously damage cerebral capillaries.*

*However, in real-world clinical practice, nephrologists have limited time, and formal cognitive screening like the Montreal Cognitive Assessment (MoCA) is rarely administered until severe dementia has already set in.*

*The objective of CKD-CI is simple: provide clinicians with an automated decision support system that calculates cognitive impairment risk using the **18 standard clinical and biochemical biomarkers** that are already drawn during routine blood and urine tests."*

---

### Slide 3: System Architecture
*"To deliver this, I built a modern, decoupled architecture:*
- *On the backend, I used **FastAPI** with Python 3.11 for asynchronous, high-throughput REST APIs, connected to an audited **SQLite database** using **SQLAlchemy ORM**.*
- *On the frontend, I engineered a responsive SaaS interface using **Next.js 14 App Router, TypeScript, and Tailwind CSS**, adhering to clinical UI standards with deep navy and clinical teal visual tokens.*
- *For the machine learning engine, I implemented four CPU-optimized models: **Logistic Regression, CatBoost, XGBoost, and Random Forest**, evaluated under 5-fold cross-validation.*
- *Importantly, the system executes **100% locally on the CPU**—there are no cloud dependencies, no expensive GPU requirements, and zero risk of patient health information leaking outside the hospital network."*

---

### Slide 4: Clinical Workflow Decoupling (Live Walkthrough)
*"A key engineering decision I made was to decouple clinical workflows into three distinct stages:*

1. *First is **Patient Registration**. This happens once. We capture patient demographics, date of birth, and detailed medical history—including diabetes type and duration, hypertension duration, cardiovascular history, and baseline CKD staging.*
2. *Second is **Clinical Encounters**. During each hospital visit, clinical staff record fresh lab measurements—such as eGFR, creatinine, BUN, and UACR. This immediately updates the patient's baseline and appends a timestamped event to their longitudinal chart.*
3. *Third is **Cognitive Assessments**. When a formal MoCA or MMSE test is conducted, it is logged separately. Here, I implemented an explicit **Target Leakage Safeguard**: ground-truth cognitive test scores are kept strictly isolated from model input vectors so the AI model never cheats.*

*Now, when a doctor navigates to the **Prediction Studio**, the system auto-assembles the patient’s profile and latest visit labs. If any of the 18 biomarkers is missing, the system doesn't guess or fill in default values—it outlines the field in amber as 'Not on Record' and requires clinical entry before computing."*

---

### Slide 5: Machine Learning Benchmarks & Calibration
*"Let’s look at the machine learning results. I trained and evaluated the models across 2,500 clinical cohort records using 5-fold stratified cross-validation:*
- *Our **Platt-Calibrated Logistic Regression** achieved the highest discriminative performance with a **Macro AUC-ROC of 89.61%** and a **Mean Brier Score of 0.1023**.*
- *Our **CatBoost** and **XGBoost** models closely followed at **88.59%** and **88.31%** AUC-ROC.*

*A critical challenge I solved during development was **probability calibration**. In early iterations, raw unscaled inputs caused softmax logits to saturate, collapsing probabilities to 99.9% for a single class. By encapsulating a `StandardScaler` inside our model pipeline, we restored well-calibrated probabilities that sum cleanly to 100% across all four risk classes: No Risk, Low Risk, Moderate Risk, and High Risk."*

---

### Slide 6: Patient Surveillance & Clinical Governance
*"Finally, patient care doesn't end with a prediction. The platform includes a complete surveillance suite:*
- *The **Clinical Overview Command Center** provides a cohort vulnerability radar and an interactive triage queue that assigns concrete care actions—such as 'Immediate MoCA & Nephrology Consult'. It also maps real patients into a live KDIGO 2024 heatmap.*
- *The **Critical Alerts** module provides provider escalation controls to acknowledge and resolve acute decline events.*
- *The **Longitudinal Trends** page tracks eGFR, albuminuria, and cognitive trajectories over time.*
- *And the **Model Governance** registry monitors live feature drift using the two-sample Kolmogorov-Smirnov test and enforces FDA Software as a Medical Device (SaMD) compliance.*

*Thank you. I would be happy to demonstrate the running application and dive into the codebase."*

---

## Section 7: Anticipated Interview Questions & Model Answers

### Q1: "Why did Logistic Regression achieve a higher AUC-ROC than XGBoost and CatBoost?"
> **Model Answer**:  
> *"In clinical tabular data where biomarkers share near-linear monotonic relationships with disease progression (for instance, lower eGFR and higher UACR monotonically increase vascular disease probability), a properly regularized and scaled linear model performs exceptionally well.  
> Gradient boosted trees excelled at capturing feature interactions, achieving ~88.5% AUC, but L2-regularized Logistic Regression coupled with StandardScaler provided better generalization on the 18-feature vector and was far easier to calibrate for probabilistic risk stratification with a lower Brier score."*

---

### Q2: "How do you handle missing values when predicting risk for a new patient?"
> **Model Answer**:  
> *"In healthcare decision support, silently imputing median or default values is dangerous because it can falsely reassure a clinician about a high-risk patient.  
> In CKD-CI, I implemented strict **Patient Data Isolation**. If a patient has only 12 of the 18 biomarkers on record, the Prediction Studio identifies the 6 missing keys, outlines them in amber as 'Not on Record — Required', and disables the inference button until the clinician either enters the missing lab values or approves baseline defaults for that evaluation."*

---

### Q3: "What measures did you take to ensure data privacy and PHI compliance?"
> **Model Answer**:  
> *"Three core measures:  
> 1. **100% Local Execution**: All models execute locally in Python via CPU multi-threading; zero patient data is ever transmitted to third-party cloud APIs.  
> 2. **PHI-Safe Logging**: Our logging middleware logs request IDs, timestamps, and model latency, but sanitizes patient names and raw biological inputs.  
> 3. **Role-Based JWT Security**: API endpoints are guarded with JSON Web Tokens and password hashing using bcrypt."*

---

### Q4: "How does the system prevent target leakage between cognitive assessments and model predictions?"
> **Model Answer**:  
> *"If an ML model is trained to predict cognitive impairment, feeding actual MoCA or MMSE screening scores into the feature set is a classic target leakage failure mode.  
> I engineered a clean architectural separation: cognitive screening scores are handled by a dedicated endpoint (`POST /patients/{id}/cognitive-assessments`) that records to the longitudinal surveillance timeline only. They are structurally excluded from the 18-biomarker feature vector consumed by `PredictionService`."*

---

### Q5: "If you had 3 more months on this project, what would you add?"
> **Model Answer**:  
> *"Three key enhancements:  
> 1. **FHIR / HL7 Integration**: Build an ingestion adapter to connect directly to hospital EHR systems (like Epic or Cerner) via SMART-on-FHIR.  
> 2. **Longitudinal Trajectory Models**: Replace cross-sectional snapshot prediction with a recurrent or temporal transformer model (like a dynamic survival analysis model) to predict the exact time-to-cognitive-decline over a 5-year window.  
> 3. **SHAP TreeExplainers**: Integrate dynamic SHAP waterfall force plots directly into the Next.js UI to give clinicians granular, patient-specific feature contribution graphics."*
