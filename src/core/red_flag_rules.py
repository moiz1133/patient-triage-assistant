from dataclasses import dataclass, field
from typing import Literal, Optional


@dataclass
class RedFlagRule:
    rule_id: str
    name: str
    description: str
    minimum_esi_floor: Literal[1, 2]
    keywords: list[str] = field(default_factory=list)


RED_FLAG_RULES: list[RedFlagRule] = [
    RedFlagRule(
        rule_id="RF001",
        name="Chest pain adult",
        description="Chest pain or pressure in adult — possible ACS",
        minimum_esi_floor=1,
        keywords=["chest pain", "chest tightness", "chest pressure"],
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
    ),
    RedFlagRule(
        rule_id="RF008",
        name="Severe abdominal pain",
        description="Severe or acute abdomen — possible surgical emergency",
        minimum_esi_floor=2,
        keywords=["severe abdominal pain", "stomach pain severe", "abdomen rigid", "guarding"],
    ),
]

_RULES_BY_ID: dict[str, RedFlagRule] = {r.rule_id: r for r in RED_FLAG_RULES}


def get_rule_by_id(rule_id: str) -> Optional[RedFlagRule]:
    return _RULES_BY_ID.get(rule_id)
