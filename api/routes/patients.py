from typing import List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from db.session import get_db
from core.deps import get_current_user, require_role
from models.patient import Patient
from models.prediction import Prediction
from models.alert import AlertEvent
from models.note import Task
from models.timeline import TimelineEvent
from schemas.patient import (
    PatientCreate,
    PatientRead,
    PatientUpdate,
    ClinicalVisitCreate,
    CognitiveAssessmentCreate,
)

router = APIRouter(prefix="/patients", tags=["patients"])


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_simple_pdf(lines: list[str]) -> bytes:
    safe_lines = [line.encode("ascii", errors="ignore").decode("ascii") for line in lines]
    text_ops = ["BT", "/F1 11 Tf", "50 760 Td", "14 TL"]
    for idx, line in enumerate(safe_lines[:45]):
        escaped = _escape_pdf_text(line)
        text_ops.append(f"({escaped}) Tj")
        if idx < len(safe_lines[:45]) - 1:
            text_ops.append("T*")
    text_ops.append("ET")
    stream = "\n".join(text_ops).encode("ascii")

    objects = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n",
        b"4 0 obj\n<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream\nendobj\n",
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        pdf.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        (
            "trailer\n"
            f"<< /Size {len(offsets)} /Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_offset}\n"
            "%%EOF\n"
        ).encode("ascii")
    )
    return bytes(pdf)


@router.post("/", response_model=PatientRead)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    existing = db.query(Patient).filter(Patient.patient_identifier == payload.patient_identifier).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Patient already exists")
    patient = Patient(
        patient_identifier=payload.patient_identifier,
        first_name=payload.first_name,
        last_name=payload.last_name,
        date_of_birth=payload.date_of_birth,
        sex=payload.sex,
        medical_history=payload.medical_history,
        features=payload.features,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    # Automatically add an intake timeline event
    try:
        intake_event = TimelineEvent(
            patient_id=patient.id,
            source_type="intake",
            summary=f"Patient enrolled: {patient.first_name or ''} {patient.last_name or ''} ({patient.patient_identifier})",
            payload={"medical_history": payload.medical_history or {}},
        )
        db.add(intake_event)
        db.commit()
    except Exception:
        db.rollback()

    return patient


@router.put("/{patient_id}", response_model=PatientRead)
def update_patient(
    patient_id: int,
    payload: PatientUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    if payload.first_name is not None:
        patient.first_name = payload.first_name
    if payload.last_name is not None:
        patient.last_name = payload.last_name
    if payload.date_of_birth is not None:
        patient.date_of_birth = payload.date_of_birth
    if payload.sex is not None:
        patient.sex = payload.sex
    if payload.medical_history is not None:
        patient.medical_history = payload.medical_history
    if payload.features is not None:
        current_features = dict(patient.features or {})
        current_features.update(payload.features)
        patient.features = current_features

    db.commit()
    db.refresh(patient)
    return patient


@router.post("/{patient_id}/visits", response_model=Dict[str, Any])
def record_clinical_visit(
    patient_id: int,
    payload: ClinicalVisitCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    visit_dict = payload.dict(exclude_none=True)
    visit_date = payload.visit_date or datetime.utcnow().strftime("%Y-%m-%d")

    # Update patient's current telemetry features with newly recorded measurements
    current_features = dict(patient.features or {})
    for key in [
        "systolic_bp", "bmi", "eGFR", "creatinine", "bun", "uacr",
        "potassium", "phosphate", "calcium", "hemoglobin", "albumin", "hsCRP"
    ]:
        if key in visit_dict and visit_dict[key] is not None:
            current_features[key] = visit_dict[key]
    patient.features = current_features

    # Log to longitudinal clinical timeline
    summary_parts = []
    if payload.eGFR is not None:
        summary_parts.append(f"eGFR: {payload.eGFR}")
    if payload.creatinine is not None:
        summary_parts.append(f"Cr: {payload.creatinine}")
    if payload.uacr is not None:
        summary_parts.append(f"UACR: {payload.uacr}")
    summary_text = f"Clinical Encounter Labs — {', '.join(summary_parts)}" if summary_parts else "Clinical Encounter Labs Recorded"

    timeline_event = TimelineEvent(
        patient_id=patient.id,
        source_type="clinical_visit",
        event_time=datetime.utcnow(),
        summary=summary_text,
        payload={
            "visit_date": visit_date,
            "measurements": visit_dict,
            "notes": payload.notes or "Routine clinical visit",
        },
    )
    db.add(timeline_event)
    db.commit()
    db.refresh(patient)

    return {
        "status": "success",
        "message": "Clinical visit and laboratory measurements recorded successfully",
        "patient_id": patient.id,
        "features": patient.features,
    }


@router.post("/{patient_id}/cognitive-assessments", response_model=Dict[str, Any])
def record_cognitive_assessment(
    patient_id: int,
    payload: CognitiveAssessmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    assessment_dict = payload.dict(exclude_none=True)
    assessment_date = payload.assessment_date or datetime.utcnow().strftime("%Y-%m-%d")

    # Note: Deliberately DOES NOT touch patient.features (input features for ML)
    # to maintain strict separation and prevent predictive target leakage.
    scores = []
    if payload.moca_score is not None:
        scores.append(f"MoCA: {payload.moca_score}/30")
    if payload.mmse_score is not None:
        scores.append(f"MMSE: {payload.mmse_score}/30")
    if payload.clinical_outcome:
        scores.append(f"Impression: {payload.clinical_outcome}")

    summary_text = f"Cognitive Screening: {', '.join(scores)}" if scores else "Formal Cognitive Assessment"

    timeline_event = TimelineEvent(
        patient_id=patient.id,
        source_type="cognitive_assessment",
        event_time=datetime.utcnow(),
        summary=summary_text,
        payload={
            "assessment_date": assessment_date,
            "scores": assessment_dict,
            "notes": payload.examiner_notes or "Formal neurocognitive screening performed",
            "target_leakage_safeguard": "Isolated from AI model input features",
        },
    )
    db.add(timeline_event)
    db.commit()

    return {
        "status": "success",
        "message": "Cognitive assessment logged to clinical timeline (safeguarded against model target leakage)",
        "patient_id": patient.id,
    }


@router.get("/{patient_id}", response_model=PatientRead)
def get_patient(patient_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


@router.get("/{patient_id}/report.pdf")
def patient_report_pdf(patient_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    latest_prediction = (
        db.query(Prediction)
        .filter(Prediction.patient_id == patient.id)
        .order_by(Prediction.created_at.desc())
        .first()
    )
    open_alerts = (
        db.query(AlertEvent)
        .filter(AlertEvent.patient_id == patient.id, AlertEvent.status != "resolved")
        .count()
    )
    open_tasks = (
        db.query(Task)
        .filter(Task.patient_id == patient.id, Task.status != "done")
        .count()
    )

    full_name = f"{patient.first_name or ''} {patient.last_name or ''}".strip() or "Unknown Patient"
    lines = [
        "CKD-CI Clinical Summary Report",
        "",
        f"Patient Name: {full_name}",
        f"Patient ID: {patient.patient_identifier}",
        f"DOB: {patient.date_of_birth or 'N/A'}",
        f"Sex: {patient.sex or 'N/A'}",
        "",
        f"Open Alerts: {open_alerts}",
        f"Open Tasks: {open_tasks}",
    ]

    if latest_prediction:
        lines.extend(
            [
                "",
                "Latest Prediction",
                f"Label: {latest_prediction.predicted_label}",
                f"Confidence: {round(float(latest_prediction.confidence or 0), 2)}",
                f"Model: {latest_prediction.model_name} ({latest_prediction.model_version})",
                f"Timestamp: {latest_prediction.created_at.isoformat() if latest_prediction.created_at else 'N/A'}",
            ]
        )
    else:
        lines.extend(["", "Latest Prediction", "No predictions recorded yet."])

    pdf_bytes = _build_simple_pdf(lines)
    filename = f"patient-{patient.patient_identifier}-report.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/", response_model=List[PatientRead])
def list_patients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    patients = db.query(Patient).offset(skip).limit(limit).all()
    return patients
