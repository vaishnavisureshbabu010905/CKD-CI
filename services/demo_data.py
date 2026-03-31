from __future__ import annotations

from models.alert import AlertEvent
from models.chat import ChatMessage, ChatThread
from models.note import Task
from models.patient import Patient
from models.prediction import Prediction
from models.timeline import TimelineEvent
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
                features={"egfr": 48, "creatinine": 1.8, "uacr": 240},
            ),
            Patient(
                patient_identifier="CKD-1002",
                first_name="David",
                last_name="Okoro",
                date_of_birth="1965-09-03",
                sex="male",
                features={"egfr": 36, "creatinine": 2.2, "uacr": 390},
            ),
            Patient(
                patient_identifier="CKD-1003",
                first_name="Sara",
                last_name="Ibrahim",
                date_of_birth="1981-02-21",
                sex="female",
                features={"egfr": 57, "creatinine": 1.4, "uacr": 140},
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

    db.commit()