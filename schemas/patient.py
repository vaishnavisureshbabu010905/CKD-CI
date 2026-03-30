from typing import Optional, Dict, Any
from pydantic import BaseModel


class PatientBase(BaseModel):
    patient_identifier: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    sex: Optional[str] = None
    features: Optional[Dict[str, Any]] = None


class PatientCreate(PatientBase):
    pass


class PatientRead(PatientBase):
    id: int

    class Config:
        orm_mode = True


class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    features: Optional[Dict[str, Any]] = None
