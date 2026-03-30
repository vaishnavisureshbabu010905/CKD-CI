from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.session import get_db
from core.deps import get_current_user, require_role
from models.patient import Patient
from schemas.patient import PatientCreate, PatientRead

router = APIRouter(prefix="/patients", tags=["patients"])


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


@router.get("/", response_model=List[PatientRead])
def list_patients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    patients = db.query(Patient).offset(skip).limit(limit).all()
    return patients
