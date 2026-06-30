from dataclasses import dataclass, field
from typing import Optional

from src.core.logger import logger
from src.layers.extraction import extract_patient_case
from src.layers.red_flag_matcher import RedFlagMatch, evaluate_all_rules, get_minimum_esi_floor
from src.models import PatientCase


@dataclass
class IntakeResult:
    patient_case: PatientCase
    red_flag_matches: list[RedFlagMatch]
    minimum_esi_floor: Optional[int]


def run_intake_pipeline(raw_intake_text: str) -> IntakeResult:
    patient_case = extract_patient_case(raw_intake_text)
    matches = evaluate_all_rules(patient_case)
    floor = get_minimum_esi_floor(matches)

    logger.info(
        "Intake pipeline complete | patient_id={} confidence={} red_flags={} esi_floor={}",
        patient_case.patient_id,
        patient_case.extraction_confidence,
        len(matches),
        floor if floor is not None else "none",
    )

    return IntakeResult(
        patient_case=patient_case,
        red_flag_matches=matches,
        minimum_esi_floor=floor,
    )
