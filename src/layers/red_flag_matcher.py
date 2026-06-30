import operator as op
from dataclasses import dataclass
from typing import Optional

from src.core.logger import log_triage_event, logger
from src.core.red_flag_rules import RED_FLAG_RULES, RedFlagRule
from src.models import PatientCase

_OPERATORS = {
    "<": op.lt,
    ">": op.gt,
    "<=": op.le,
    ">=": op.ge,
    "==": op.eq,
}


@dataclass
class RedFlagMatch:
    rule_id: str
    rule_name: str
    minimum_esi_floor: int
    trigger_reason: str


def check_keyword_match(rule: RedFlagRule, case: PatientCase) -> Optional[str]:
    if not rule.keywords:
        return None

    search_fields = [("chief_complaint", case.chief_complaint)] + [
        ("symptom", s.name) for s in case.symptoms
    ]
    for keyword in rule.keywords:
        kw_lower = keyword.lower()
        for field_label, text in search_fields:
            if kw_lower in text.lower():
                return f"keyword '{keyword}' found in {field_label}"
    return None


def check_vital_condition(rule: RedFlagRule, case: PatientCase) -> Optional[str]:
    if rule.vital_conditions is None:
        return None

    reasons: list[str] = []
    for field_name, (operator_str, threshold) in rule.vital_conditions.items():
        value = getattr(case.vitals, field_name, None)
        if value is None:
            continue
        comparator = _OPERATORS[operator_str]
        if comparator(value, threshold):
            reasons.append(f"{field_name} {value} {operator_str} {threshold}")

    return "; ".join(reasons) if reasons else None


def check_age_constraint(rule: RedFlagRule, case: PatientCase) -> bool:
    has_constraint = rule.min_age is not None or rule.max_age is not None
    if not has_constraint:
        return True
    if case.age is None:
        # Unknown age — fail open toward safety, rule can still apply
        return True
    if rule.min_age is not None and case.age < rule.min_age:
        return False
    if rule.max_age is not None and case.age > rule.max_age:
        return False
    return True


def evaluate_rule(rule: RedFlagRule, case: PatientCase) -> Optional[RedFlagMatch]:
    if not check_age_constraint(rule, case):
        return None

    keyword_reason = check_keyword_match(rule, case)
    vital_reason = check_vital_condition(rule, case)

    if keyword_reason is None and vital_reason is None:
        return None

    parts = [r for r in (keyword_reason, vital_reason) if r is not None]
    trigger_reason = "; ".join(parts)

    return RedFlagMatch(
        rule_id=rule.rule_id,
        rule_name=rule.name,
        minimum_esi_floor=rule.minimum_esi_floor,
        trigger_reason=trigger_reason,
    )


def evaluate_all_rules(case: PatientCase) -> list[RedFlagMatch]:
    matches: list[RedFlagMatch] = []

    for rule in RED_FLAG_RULES:
        match = evaluate_rule(rule, case)
        if match is None:
            continue
        matches.append(match)
        logger.warning(
            "Red flag triggered | patient_id={} rule_id={} rule_name={!r} esi_floor={} reason={!r}",
            case.patient_id,
            match.rule_id,
            match.rule_name,
            match.minimum_esi_floor,
            match.trigger_reason,
        )
        log_triage_event(
            event_type="red_flag_triggered",
            patient_id=case.patient_id,
            details={
                "rule_id": match.rule_id,
                "rule_name": match.rule_name,
                "trigger_reason": match.trigger_reason,
                "minimum_esi_floor": match.minimum_esi_floor,
            },
        )

    if not matches:
        logger.info("No red flags triggered for patient {}", case.patient_id)

    return matches


def get_minimum_esi_floor(matches: list[RedFlagMatch]) -> Optional[int]:
    if not matches:
        return None
    return min(m.minimum_esi_floor for m in matches)
