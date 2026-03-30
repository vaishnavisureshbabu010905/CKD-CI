from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class PredictionRequest(BaseModel):
    patient_identifier: Optional[str] = None
    features: Dict[str, Any]


class PredictionResult(BaseModel):
    predicted_label: str
    probabilities: Dict[str, float]
    confidence: Optional[float] = None
    explanation: Optional[Dict[str, Any]] = None


class PredictionResponse(BaseModel):
    prediction_id: Optional[int] = None
    patient_identifier: Optional[str] = None
    result: PredictionResult
    model_name: str
    model_version: str


class BatchPredictionRequest(BaseModel):
    items: List[PredictionRequest]


class BatchPredictionResponse(BaseModel):
    results: List[PredictionResponse]
