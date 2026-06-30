import pytest
from pydantic import ValidationError

from src.models import PatientCase, Symptom, TriageOutput, Vitals

# --- helpers ---

def _minimal_patient(**overrides) -> dict:
    base = {
        "chief_complaint": "headache",
        "raw_input_text": "Patient reports headache since this morning.",
        "extraction_confidence": 0.9,
    }
    return {**base, **overrides}


def _minimal_triage(**overrides) -> dict:
    base = {
        "patient_id": "test-pid-001",
        "esi_level": 3,
        "routing_suggestion": "Urgent care",
        "reasoning": "Moderate symptoms, no red flags.",
        "confidence_score": 0.85,
    }
    return {**base, **overrides}


# --- PatientCase ---

def test_patient_case_defaults():
    case = PatientCase(**_minimal_patient())
    assert case.patient_id  # auto-generated
    assert len(case.patient_id) == 36  # UUID4 string length
    assert case.symptoms == []
    vitals = case.vitals
    assert vitals.systolic_bp is None
    assert vitals.diastolic_bp is None
    assert vitals.heart_rate is None
    assert vitals.respiratory_rate is None
    assert vitals.temperature_celsius is None
    assert vitals.oxygen_saturation is None


def test_patient_case_full():
    case = PatientCase(
        chief_complaint="chest pain",
        raw_input_text="55yo male with crushing chest pain radiating to left arm, onset 30 mins ago.",
        extraction_confidence=0.95,
        age=55,
        sex="male",
        symptoms=[
            Symptom(name="chest pain", duration_hours=0.5, severity="severe", onset="sudden", is_worsening=True)
        ],
        vitals=Vitals(systolic_bp=150, diastolic_bp=95, heart_rate=102, oxygen_saturation=97.0),
        current_medications=["aspirin", "metoprolol"],
        known_allergies=["penicillin"],
        relevant_medical_history=["hypertension", "previous MI"],
    )
    data = case.model_dump()
    assert isinstance(data, dict)
    assert data["chief_complaint"] == "chest pain"
    assert data["age"] == 55


def test_symptom_severity_validation():
    with pytest.raises(ValidationError):
        Symptom(name="pain", severity="critical")


def test_extraction_confidence_bounds():
    with pytest.raises(ValidationError):
        PatientCase(**_minimal_patient(extraction_confidence=1.5))


# --- TriageOutput ---

def test_esi_label_auto_computed():
    output = TriageOutput(**_minimal_triage(esi_level=2, confidence_score=0.8))
    assert output.esi_label == "Emergent"


def test_requires_human_review_true():
    output = TriageOutput(**_minimal_triage(esi_level=1, confidence_score=0.9))
    assert output.requires_human_review is True


def test_requires_human_review_low_confidence():
    output = TriageOutput(**_minimal_triage(esi_level=4, confidence_score=0.5))
    assert output.requires_human_review is True
