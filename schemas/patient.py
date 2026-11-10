from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class PatientBase(BaseModel):
    patient_identifier: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    sex: Optional[str] = None
    features: Optional[Dict[str, Any]] = None
    medical_history: Optional[Dict[str, Any]] = None


class PatientCreate(PatientBase):
    pass


class PatientRead(PatientBase):
    id: int

    class Config:
        orm_mode = True


class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    sex: Optional[str] = None
    features: Optional[Dict[str, Any]] = None
    medical_history: Optional[Dict[str, Any]] = None


class ClinicalVisitCreate(BaseModel):
    visit_date: Optional[str] = None
    systolic_bp: Optional[float] = None
    bmi: Optional[float] = None
    eGFR: Optional[float] = None
    creatinine: Optional[float] = None
    bun: Optional[float] = None
    uacr: Optional[float] = None
    potassium: Optional[float] = None
    phosphate: Optional[float] = None
    calcium: Optional[float] = None
    hemoglobin: Optional[float] = None
    albumin: Optional[float] = None
    hsCRP: Optional[float] = None
    notes: Optional[str] = None


class CognitiveAssessmentCreate(BaseModel):
    assessment_date: Optional[str] = None
    moca_score: Optional[float] = None
    mmse_score: Optional[float] = None
    dsst_score: Optional[float] = None
    cerad_score: Optional[str] = None
    clinical_outcome: Optional[str] = None
    examiner_notes: Optional[str] = None
