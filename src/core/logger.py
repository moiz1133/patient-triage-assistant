import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger

from src.config import config

_CONSOLE_FORMAT = "{time:HH:mm:ss} | {level:<8} | {name}:{line} — {message}"
_LOG_DIR = Path("logs")
_LOG_DIR.mkdir(exist_ok=True)

# Remove loguru's default stderr sink before adding our own
logger.remove()

logger.add(
    sys.stderr,
    level=config.log_level,
    format=_CONSOLE_FORMAT,
    colorize=True,
)

logger.add(
    _LOG_DIR / "app.log",
    level="DEBUG",
    format=_CONSOLE_FORMAT,
    rotation="10 MB",
    retention="7 days",
    colorize=False,
)

_AUDIT_LOG = _LOG_DIR / "triage_events.jsonl"


def log_triage_event(event_type: str, patient_id: str, details: dict) -> None:
    """Append a structured audit record to triage_events.jsonl."""
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "patient_id": patient_id,
        "details": details,
    }
    with _AUDIT_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    logger.debug("triage_event | type={} patient_id={}", event_type, patient_id)
