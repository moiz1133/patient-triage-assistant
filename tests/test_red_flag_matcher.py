from unittest.mock import patch

import pytest

from src.core.red_flag_rules import get_rule_by_id
from src.layers.red_flag_matcher import (
    RedFlagMatch,
    check_keyword_match,
    check_vital_condition,
    evaluate_all_rules,
    evaluate_rule,
    get_minimum_esi_floor,
)
from src.models import PatientCase, Symptom, Vitals


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _case(**kwargs) -> PatientCase:
    defaults = {
        "chief_complaint": "unspecified complaint",
        "raw_input_text": "(test)",
        "extraction_confidence": 1.0,
    }
    return PatientCase(**{**defaults, **kwargs})


# ---------------------------------------------------------------------------
# Tests 1–3: chest pain age variants (parametrized)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("age,must_have,must_not_have", [
    (60, {"RF001", "RF009"}, set()),       # test 1: elderly — both rules fire
    (25, {"RF009"},          {"RF001"}),   # test 2: young — RF001 gated by min_age=45
    (25, {"RF009"},          set()),       # test 3: young — RF009 (no age gate) still fires
])
def test_chest_pain_age_variants(age, must_have, must_not_have):
    case = _case(age=age, chief_complaint="chest pain", symptoms=[Symptom(name="chest pain")])
    matches = evaluate_all_rules(case)
    triggered = {m.rule_id for m in matches}
    assert must_have <= triggered, f"expected {must_have} to be triggered, got {triggered}"
    assert not (must_not_have & triggered), f"expected {must_not_have} NOT to trigger, got {triggered}"


# ---------------------------------------------------------------------------
# Test 4: stroke keywords
# ---------------------------------------------------------------------------

def test_stroke_keywords_trigger_rf002():
    case = _case(
        chief_complaint="sudden facial droop and arm weakness",
        symptoms=[Symptom(name="facial droop"), Symptom(name="arm weakness")],
    )
    matches = evaluate_all_rules(case)
    assert any(m.rule_id == "RF002" for m in matches)


# ---------------------------------------------------------------------------
# Test 5: vital-only trigger (oxygen) — no matching keyword in text
# ---------------------------------------------------------------------------

def test_low_oxygen_triggers_via_vitals_without_keyword():
    case = _case(
        chief_complaint="feeling unwell",   # contains none of RF003's keywords
        vitals=Vitals(oxygen_saturation=88),
    )
    rule = get_rule_by_id("RF003")
    keyword_hit = check_keyword_match(rule, case)
    vital_hit = check_vital_condition(rule, case)

    assert keyword_hit is None, "keyword should not match on neutral complaint"
    assert vital_hit is not None, "vital condition should trigger on SpO2=88 < 92"

    matches = evaluate_all_rules(case)
    assert any(m.rule_id == "RF003" for m in matches)


# ---------------------------------------------------------------------------
# Test 6: all-None vitals must NOT trigger a vital-based rule
# ---------------------------------------------------------------------------

def test_missing_vitals_does_not_trigger_vital_rule():
    case = _case(chief_complaint="feeling unwell", vitals=Vitals())
    rule = get_rule_by_id("RF010")  # systolic_bp < 90, keywords=[]
    result = evaluate_rule(rule, case)
    assert result is None, "rule must not fire when the relevant vital is None"


# ---------------------------------------------------------------------------
# Test 7: hypotension
# ---------------------------------------------------------------------------

def test_hypotension_triggers_rf010():
    case = _case(chief_complaint="dizziness", vitals=Vitals(systolic_bp=85))
    matches = evaluate_all_rules(case)
    assert any(m.rule_id == "RF010" for m in matches)


# ---------------------------------------------------------------------------
# Test 8: suicidal ideation
# ---------------------------------------------------------------------------

def test_suicidal_ideation_triggers_rf013():
    case = _case(chief_complaint="patient reports wanting to end my life")
    matches = evaluate_all_rules(case)
    assert any(m.rule_id == "RF013" for m in matches)


# ---------------------------------------------------------------------------
# Test 9: no red flags on a benign case
# ---------------------------------------------------------------------------

def test_clean_case_zero_matches():
    case = _case(
        age=30,
        chief_complaint="mild cold symptoms",
        symptoms=[Symptom(name="runny nose")],
    )
    matches = evaluate_all_rules(case)
    assert matches == []


# ---------------------------------------------------------------------------
# Test 10: missing age fails open for age-constrained rule
# ---------------------------------------------------------------------------

def test_missing_age_fails_open_for_age_constrained_rule():
    case = _case(age=None, chief_complaint="chest pain")
    matches = evaluate_all_rules(case)
    triggered = {m.rule_id for m in matches}
    assert "RF001" in triggered, "RF001 (min_age=45) must fire when age is unknown — fail open"


# ---------------------------------------------------------------------------
# Test 11: multiple rules trigger simultaneously
# ---------------------------------------------------------------------------

def test_multiple_rules_trigger_simultaneously():
    case = _case(
        age=70,
        chief_complaint="chest pain and difficulty breathing",
        symptoms=[Symptom(name="chest pain"), Symptom(name="difficulty breathing")],
        vitals=Vitals(oxygen_saturation=89),
    )
    matches = evaluate_all_rules(case)
    triggered = {m.rule_id for m in matches}
    assert {"RF001", "RF009", "RF003"} <= triggered
    assert len(matches) >= 3


# ---------------------------------------------------------------------------
# Test 12: get_minimum_esi_floor returns the lowest (most urgent) value
# ---------------------------------------------------------------------------

def test_get_minimum_esi_floor_returns_lowest():
    matches = [
        RedFlagMatch("RF009", "Chest pain any age",  2, "keyword 'chest pain'"),
        RedFlagMatch("RF001", "Chest pain adult",    1, "keyword 'chest pain'"),
        RedFlagMatch("RF008", "Severe abdominal pain", 2, "keyword 'guarding'"),
    ]
    assert get_minimum_esi_floor(matches) == 1


# ---------------------------------------------------------------------------
# Test 13: get_minimum_esi_floor on empty list returns None
# ---------------------------------------------------------------------------

def test_get_minimum_esi_floor_empty_list_returns_none():
    assert get_minimum_esi_floor([]) is None


# ---------------------------------------------------------------------------
# Test 14: keyword matching is case-insensitive
# ---------------------------------------------------------------------------

def test_keyword_match_is_case_insensitive():
    case = _case(chief_complaint="CHEST PAIN")
    rule = get_rule_by_id("RF009")
    result = check_keyword_match(rule, case)
    assert result is not None, "keyword match must be case-insensitive"

    matches = evaluate_all_rules(case)
    assert any(m.rule_id == "RF009" for m in matches)


# ---------------------------------------------------------------------------
# Test 15: audit log called once per triggered rule
# ---------------------------------------------------------------------------

def test_audit_log_called_for_each_match():
    case = _case(
        age=60,
        chief_complaint="chest pain and difficulty breathing",
        symptoms=[Symptom(name="chest pain"), Symptom(name="difficulty breathing")],
        vitals=Vitals(oxygen_saturation=88),
    )
    with patch("src.layers.red_flag_matcher.log_triage_event") as mock_log:
        matches = evaluate_all_rules(case)

    assert mock_log.call_count == len(matches), (
        f"log_triage_event must be called once per match; "
        f"got {mock_log.call_count} calls for {len(matches)} matches"
    )
    for call in mock_log.call_args_list:
        args, _ = call
        assert args[0] == "red_flag_triggered"
        assert args[1] == case.patient_id


# ---------------------------------------------------------------------------
# Test 16: pediatric fever age boundary
#
# Clinical intent: RF007 targets infants under 3 months (~0.25 years).
# PatientCase.age is Optional[int], so fractional ages cannot be represented.
# The stored max_age=0 means:
#   age=0  → check_age_constraint: 0 > 0 is False → constraint PASSES → rule CAN fire
#   age=1  → check_age_constraint: 1 > 0 is True  → constraint FAILS  → rule excluded
# The effective clinical boundary is therefore age=0 (newborns only).
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("age,expect_rf007", [
    (0,    True),   # newborn — within max_age=0, rule fires
    (1,    False),  # 1-year-old — exceeds max_age=0, rule excluded
    (None, True),   # unknown age — fails open, rule can still fire
])
def test_pediatric_fever_age_boundary(age, expect_rf007):
    case = _case(
        age=age,
        chief_complaint="elevated temperature",  # deliberately avoids RF007 keywords
        vitals=Vitals(temperature_celsius=38.5),
    )
    rule = get_rule_by_id("RF007")
    match = evaluate_rule(rule, case)
    if expect_rf007:
        assert match is not None, f"RF007 should trigger for age={age}"
        assert match.rule_id == "RF007"
    else:
        assert match is None, f"RF007 should not trigger for age={age}"
