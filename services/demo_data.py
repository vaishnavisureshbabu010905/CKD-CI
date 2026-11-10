from __future__ import annotations

from models.alert import AlertEvent
from models.chat import ChatMessage, ChatThread
from models.note import Task
from models.patient import Patient
from models.prediction import Prediction
from models.timeline import TimelineEvent
from models.model_registry import ModelRegistry
from models.user import User, UserRole
from core.security import get_password_hash


def ensure_demo_data(db) -> None:
    """Seed local/demo records when the database is empty.

    This keeps the UI functional in fresh environments.
    """
    admin = db.query(User).filter(User.email == "admin@example.com").first()
    if not admin:
        admin = User(
            email="admin@example.com",
            full_name="Platform Admin",
            hashed_password=get_password_hash("change_me"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)
        db.flush()

    existing_patients = db.query(Patient).count()
    if existing_patients == 0:
        patients = [
            Patient(
                patient_identifier="CKD-1001",
                first_name="Amina",
                last_name="Rahman",
                date_of_birth="1970-04-12",
                sex="female",
                medical_history={
                    "diabetes": "No",
                    "hypertension": "Yes",
                    "hypertension_duration": 6,
                    "cvd": "No",
                    "cvd_conditions": [],
                    "ckd_diagnosis": "Yes",
                    "ckd_stage": "G3a",
                    "ckd_duration": 3,
                    "dialysis_status": "Not on dialysis",
                    "education_level": "Undergraduate / Graduate",
                },
                features={
                    "age": 56, "education_years": 14, "gender": 0,
                    "diabetes": 0, "hypertension": 1, "cvd": 0,
                    "eGFR": 48, "creatinine": 1.8, "bun": 22, "uacr": 240,
                    "hemoglobin": 11.8, "albumin": 3.9, "hsCRP": 2.1,
                    "potassium": 4.3, "phosphate": 3.8, "calcium": 9.2,
                    "systolic_bp": 148, "bmi": 26.1,
                },
            ),
            Patient(
                patient_identifier="CKD-1002",
                first_name="David",
                last_name="Okoro",
                date_of_birth="1965-09-03",
                sex="male",
                medical_history={
                    "diabetes": "Yes",
                    "diabetes_type": "Type 2",
                    "diabetes_duration": 12,
                    "hypertension": "Yes",
                    "hypertension_duration": 15,
                    "cvd": "Yes",
                    "cvd_conditions": ["Coronary artery disease (CAD)", "Heart failure"],
                    "ckd_diagnosis": "Yes",
                    "ckd_stage": "G3b",
                    "ckd_duration": 5,
                    "dialysis_status": "Not on dialysis",
                    "education_level": "Secondary education",
                },
                features={
                    "age": 61, "education_years": 10, "gender": 1,
                    "diabetes": 1, "hypertension": 1, "cvd": 1,
                    "eGFR": 36, "creatinine": 2.2, "bun": 35, "uacr": 390,
                    "hemoglobin": 10.4, "albumin": 3.4, "hsCRP": 4.8,
                    "potassium": 4.8, "phosphate": 4.6, "calcium": 9.0,
                    "systolic_bp": 162, "bmi": 29.3,
                },
            ),
            Patient(
                patient_identifier="CKD-1003",
                first_name="Sara",
                last_name="Ibrahim",
                date_of_birth="1981-02-21",
                sex="female",
                medical_history={
                    "diabetes": "No",
                    "hypertension": "No",
                    "cvd": "No",
                    "cvd_conditions": [],
                    "ckd_diagnosis": "Yes",
                    "ckd_stage": "G2",
                    "ckd_duration": 1,
                    "dialysis_status": "Not on dialysis",
                    "education_level": "Undergraduate / Graduate",
                },
                features={
                    "age": 45, "education_years": 16, "gender": 0,
                    "diabetes": 0, "hypertension": 0, "cvd": 0,
                    "eGFR": 57, "creatinine": 1.4, "bun": 18, "uacr": 140,
                    "hemoglobin": 13.1, "albumin": 4.2, "hsCRP": 1.4,
                    "potassium": 4.0, "phosphate": 3.2, "calcium": 9.5,
                    "systolic_bp": 122, "bmi": 23.8,
                },
            ),
        ]
        db.add_all(patients)
        db.flush()

    first_patient = db.query(Patient).order_by(Patient.id.asc()).first()
    if not first_patient:
        db.commit()
        return

    if db.query(Task).count() == 0:
        db.add(
            Task(
                patient_id=first_patient.id,
                title="Review CKD risk trend",
                description="Validate latest lab trajectory and care escalation plan.",
                status="open",
                priority="high",
                created_by=admin.id,
                assignee_id=admin.id,
            )
        )

    if db.query(AlertEvent).count() == 0:
        db.add(
            AlertEvent(
                patient_id=first_patient.id,
                triggered_by=admin.id,
                status="open",
                payload={"message": "Rapid eGFR decline detected in the last 90 days."},
            )
        )

    if db.query(Prediction).count() == 0:
        db.add(
            Prediction(
                patient_id=first_patient.id,
                user_id=admin.id,
                model_name="ckd_ci_model",
                model_version="v1",
                predicted_label="moderate_risk",
                probabilities={"low": 0.19, "moderate": 0.63, "high": 0.18},
                confidence=0.63,
                input_features=first_patient.features or {},
            )
        )

    if db.query(TimelineEvent).filter(TimelineEvent.patient_id == first_patient.id).count() == 0:
        db.add_all(
            [
                TimelineEvent(
                    patient_id=first_patient.id,
                    source_type="note",
                    summary="Initial CKD care plan created and baseline labs reviewed.",
                    payload={"phase": "intake"},
                ),
                TimelineEvent(
                    patient_id=first_patient.id,
                    source_type="alert",
                    summary="Rapid eGFR decline triggered a high-priority alert.",
                    payload={"severity": "high"},
                ),
                TimelineEvent(
                    patient_id=first_patient.id,
                    source_type="prediction",
                    summary="Latest model run indicates moderate CKD progression risk.",
                    payload={"label": "moderate_risk"},
                ),
            ]
        )

    thread = db.query(ChatThread).order_by(ChatThread.id.asc()).first()
    if not thread:
        thread = ChatThread(
            thread_type="patient",
            patient_id=first_patient.id,
            name="Care Team - CKD-1001",
            participants=[admin.id],
        )
        db.add(thread)
        db.flush()

    if db.query(ChatMessage).filter(ChatMessage.thread_id == thread.id).count() == 0:
        db.add(
            ChatMessage(
                thread_id=thread.id,
                sender_id=None,
                content="Welcome. I can summarize risk and suggest next care actions.",
                status="delivered",
            )
        )

    if db.query(ModelRegistry).count() == 0:
        models = [
            ModelRegistry(
                model_name="Multiclass Logistic Regression (L2)",
                version="v1.0.0-calibrated",
                artifact_path="results/model_bundle.pkl",
                is_active=True,
                meta={"stage": "prod", "framework": "Scikit-Learn", "task": "Multiclass Cognitive Stratification"},
                metrics_json={
                    "auc_roc": 0.8961,
                    "f1_macro": 0.6597,
                    "accuracy": 0.7000,
                    "brier_score": 0.1023,
                    "log_loss": 0.6785,
                    "calibration": "Platt Sigmoidal Calibrated",
                },
            ),
            ModelRegistry(
                model_name="CatBoost Classifier",
                version="v1.0.0",
                artifact_path="models/catboost.pkl",
                is_active=False,
                meta={"stage": "staging", "framework": "CatBoost", "task": "Multiclass Cognitive Stratification"},
                metrics_json={
                    "auc_roc": 0.8859,
                    "f1_macro": 0.6232,
                    "accuracy": 0.6560,
                    "brier_score": 0.1070,
                    "log_loss": 0.7163,
                    "calibration": "MultiClass Hist Tree",
                },
            ),
            ModelRegistry(
                model_name="XGBoost Classifier",
                version="v1.0.0",
                artifact_path="models/xgboost.pkl",
                is_active=False,
                meta={"stage": "candidate", "framework": "XGBoost", "task": "Multiclass Cognitive Stratification"},
                metrics_json={
                    "auc_roc": 0.8831,
                    "f1_macro": 0.6409,
                    "accuracy": 0.6740,
                    "brier_score": 0.1103,
                    "log_loss": 0.7311,
                    "calibration": "Histogram Softprob",
                },
            ),
            ModelRegistry(
                model_name="Random Forest Classifier",
                version="v1.0.0",
                artifact_path="models/random_forest.pkl",
                is_active=False,
                meta={"stage": "baseline", "framework": "Scikit-Learn", "task": "Multiclass Cognitive Stratification"},
                metrics_json={
                    "auc_roc": 0.8782,
                    "f1_macro": 0.6374,
                    "accuracy": 0.6820,
                    "brier_score": 0.1122,
                    "log_loss": 0.7802,
                    "calibration": "Balanced Ensemble",
                },
            ),
        ]
        db.add_all(models)

    db.commit()