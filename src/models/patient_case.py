from datetime import datetime
from typing import Literal, Optional
from uuid import uuid4

from pydantic import ConfigDict, Field, model_validator

from pydantic import BaseModel


_ESI_LABELS: dict[int, str] = {
    1: "Resuscitation",
    2: "Emergent",
    3: "Urgent",
    4: "Less Urgent",
    5: "Non-Urgent",
}


class Symptom(BaseModel):
    name: str
    duration_hours: Optional[float] = None
    severity: Optional[Literal["mild", "moderate", "severe"]] = None
    onset: Optional[Literal["sudden", "gradual"]] = None
    is_worsening: Optional[bool] = None


class Vitals(BaseModel):
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    heart_rate: Optional[int] = None
    respiratory_rate: Optional[int] = None
    temperature_celsius: Optional[float] = None
    oxygen_saturation: Optional[float] = None


class PatientCase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    patient_id: str = Field(default_factory=lambda: str(uuid4()))
    age: Optional[int] = None
    sex: Optional[Literal["male", "female", "other", "unknown"]] = None
    chief_complaint: str
    symptoms: list[Symptom] = []
    vitals: Vitals = Field(default_factory=Vitals)
    current_medications: list[str] = []
    known_allergies: list[str] = []
    relevant_medical_history: list[str] = []
    raw_input_text: str
    extraction_confidence: float = Field(ge=0.0, le=1.0)


class TriageOutput(BaseModel):
    patient_id: str
    esi_level: Literal[1, 2, 3, 4, 5]
    esi_label: str = ""
    routing_suggestion: str
    reasoning: str
    red_flags_triggered: list[str] = []
    retrieved_chunks: list[str] = []
    confidence_score: float = Field(ge=0.0, le=1.0)
    requires_human_review: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @model_validator(mode="after")
    def _compute_derived_fields(self) -> "TriageOutput":
        self.esi_label = _ESI_LABELS[self.esi_level]
        self.requires_human_review = self.confidence_score < 0.7 or self.esi_level <= 2
        return self
