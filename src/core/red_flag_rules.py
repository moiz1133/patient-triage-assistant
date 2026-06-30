from dataclasses import dataclass, field
from typing import Literal, Optional


@dataclass
class RedFlagRule:
    rule_id: str
    name: str
    description: str
    minimum_esi_floor: Literal[1, 2]
    keywords: list[str] = field(default_factory=list)
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    # {field_name: (operator, threshold)}, operator in ["<", ">", "<=", ">=", "=="]
    # Vital conditions are OR'd with keywords — either path can trigger the rule.
    vital_conditions: Optional[dict] = None


RED_FLAG_RULES: list[RedFlagRule] = [
    RedFlagRule(
        rule_id="RF001",
        name="Chest pain adult",
        description="Chest pain or pressure in adult — possible ACS",
        minimum_esi_floor=1,
        keywords=["chest pain", "chest tightness", "chest pressure"],
        min_age=45,
    ),
    RedFlagRule(
        rule_id="RF002",
        name="FAST stroke symptoms",
        description="FAST stroke criteria — face drooping, arm weakness, speech difficulty",
        minimum_esi_floor=1,
        keywords=["facial droop", "arm weakness", "speech slurred", "sudden confusion", "vision loss"],
    ),
    RedFlagRule(
        rule_id="RF003",
        name="Respiratory distress",
        description="Severe respiratory distress or oxygen saturation concern",
        minimum_esi_floor=1,
        keywords=["difficulty breathing", "can't breathe", "shortness of breath severe", "oxygen", "blue lips"],
        vital_conditions={"oxygen_saturation": ("<", 92)},
    ),
    RedFlagRule(
        rule_id="RF004",
        name="Severe bleeding",
        description="Uncontrolled or severe bleeding",
        minimum_esi_floor=1,
        keywords=["uncontrolled bleeding", "heavy bleeding", "blood loss", "hemorrhage"],
    ),
    RedFlagRule(
        rule_id="RF005",
        name="Altered consciousness",
        description="Loss of consciousness or unresponsive patient",
        minimum_esi_floor=1,
        keywords=["unconscious", "unresponsive", "not waking", "seizure", "collapse"],
    ),
    RedFlagRule(
        rule_id="RF006",
        name="Anaphylaxis",
        description="Signs of anaphylaxis or severe allergic reaction",
        minimum_esi_floor=1,
        keywords=["allergic reaction severe", "throat swelling", "anaphylaxis", "epipen", "can't swallow"],
    ),
    RedFlagRule(
        rule_id="RF007",
        name="Pediatric fever",
        description="Fever in infant under 3 months — requires urgent assessment",
        minimum_esi_floor=2,
        keywords=["fever", "high temperature"],
        max_age=0,  # stored as int per dataclass type; matching logic must treat age <= 0.25 years
        vital_conditions={"temperature_celsius": (">=", 38.0)},
    ),
    RedFlagRule(
        rule_id="RF008",
        name="Severe abdominal pain",
        description="Severe or acute abdomen — possible surgical emergency",
        minimum_esi_floor=2,
        keywords=["severe abdominal pain", "stomach pain severe", "abdomen rigid", "guarding"],
    ),
    RedFlagRule(
        rule_id="RF009",
        name="Chest pain any age",
        description="Chest pain in any patient — baseline urgent triage even without age trigger",
        minimum_esi_floor=2,
        keywords=["chest pain", "chest tightness", "chest pressure"],
    ),
    RedFlagRule(
        rule_id="RF010",
        name="Hypotension",
        description="Systolic blood pressure below 90 — possible shock",
        minimum_esi_floor=1,
        keywords=[],
        vital_conditions={"systolic_bp": ("<", 90)},
    ),
    RedFlagRule(
        rule_id="RF011",
        name="Tachycardia severe",
        description="Heart rate above 130 bpm at rest",
        minimum_esi_floor=2,
        keywords=[],
        vital_conditions={"heart_rate": (">", 130)},
    ),
    RedFlagRule(
        rule_id="RF012",
        name="High fever adult",
        description="High fever in adult — possible sepsis risk",
        minimum_esi_floor=2,
        keywords=[],
        min_age=18,
        vital_conditions={"temperature_celsius": (">=", 39.5)},
    ),
    RedFlagRule(
        rule_id="RF013",
        name="Suicidal ideation",
        description="Expressed suicidal ideation or self-harm intent — requires urgent mental health evaluation",
        minimum_esi_floor=2,
        keywords=["suicidal", "want to die", "kill myself", "self harm", "end my life"],
    ),
    RedFlagRule(
        rule_id="RF014",
        name="Pregnancy complication",
        description="Pregnancy with bleeding, severe pain, or reduced fetal movement",
        minimum_esi_floor=2,
        keywords=["pregnant bleeding", "pregnancy bleeding", "severe pregnancy pain", "reduced fetal movement"],
    ),
]

_RULES_BY_ID: dict[str, RedFlagRule] = {r.rule_id: r for r in RED_FLAG_RULES}


def get_rule_by_id(rule_id: str) -> Optional[RedFlagRule]:
    return _RULES_BY_ID.get(rule_id)
