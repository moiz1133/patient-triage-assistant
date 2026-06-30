from src.core.llm_client import LLMExtractionError, call_structured
from src.core.logger import logger
from src.layers.extraction_prompts import EXTRACTION_SYSTEM_PROMPT, build_extraction_prompt
from src.models import PatientCase

_MAX_INPUT_CHARS = 5000


def extract_patient_case(raw_intake_text: str) -> PatientCase:
    if raw_intake_text is None:
        raise ValueError("intake text cannot be None")

    original_text = raw_intake_text
    stripped = raw_intake_text.strip()

    if not stripped:
        logger.warning("extract_patient_case received empty input — skipping LLM call")
        return PatientCase(
            chief_complaint="No information provided",
            raw_input_text=original_text,
            extraction_confidence=0.0,
        )

    if len(stripped) > _MAX_INPUT_CHARS:
        logger.warning(
            "Input text truncated from {} to {} chars to prevent prompt-stuffing",
            len(stripped),
            _MAX_INPUT_CHARS,
        )
        stripped = stripped[:_MAX_INPUT_CHARS]

    try:
        user_prompt = build_extraction_prompt(stripped)
        case: PatientCase = call_structured(
            system_prompt=EXTRACTION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=PatientCase,
        )
        # Overwrite LLM-generated raw_input_text with ground truth original
        case.raw_input_text = original_text

        logger.info(
            "Extraction complete | patient_id={} chief_complaint={!r} confidence={}",
            case.patient_id,
            case.chief_complaint,
            case.extraction_confidence,
        )
        return case

    except LLMExtractionError as exc:
        logger.error(
            "Extraction failed — returning fallback | input_preview={!r} | error={}",
            original_text[:200],
            exc,
        )
        return PatientCase(
            chief_complaint="Extraction failed — manual review required",
            raw_input_text=original_text,
            extraction_confidence=0.0,
        )


def extract_patient_cases_batch(raw_texts: list[str]) -> list[PatientCase]:
    results: list[PatientCase] = []
    for text in raw_texts:
        results.append(extract_patient_case(text))

    low_confidence = sum(1 for c in results if c.extraction_confidence < 0.5)
    logger.info(
        "Batch extraction complete | total={} low_confidence(<0.5)={}",
        len(results),
        low_confidence,
    )
    return results
