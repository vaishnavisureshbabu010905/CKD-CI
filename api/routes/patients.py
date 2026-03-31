from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from db.session import get_db
from core.deps import get_current_user, require_role
from models.patient import Patient
from models.prediction import Prediction
from models.alert import AlertEvent
from models.note import Task
from schemas.patient import PatientCreate, PatientRead

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
def create_patient(payload: PatientCreate, db: Session = Depends(get_db), current_user=Depends(require_role("lab_technician"))):
    existing = db.query(Patient).filter(Patient.patient_identifier == payload.patient_identifier).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Patient already exists")
    patient = Patient(
        patient_identifier=payload.patient_identifier,
        first_name=payload.first_name,
        last_name=payload.last_name,
        date_of_birth=payload.date_of_birth,
        sex=payload.sex,
        features=payload.features,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


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
