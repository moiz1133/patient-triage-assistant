# Patient Intake Triage Assistant

An AI-powered decision-support tool for front-desk staff at small clinics. It reads free-text patient intake forms and outputs an ESI urgency level (1–5), a specialist routing suggestion, and any red-flag alerts that apply — giving staff the information they need to prioritise patients quickly and safely. The system is designed for decision-support only: a qualified staff member always reviews and confirms the output before any action is taken.

---

## Architecture

A four-layer pipeline processes each intake form end-to-end:

- **Layer 1 — Input Parsing:** GPT-4o-mini extracts structured fields (symptoms, vitals, medications) from free text and returns a validated `PatientCase` object via Pydantic.
- **Layer 2 — Red-Flag Detection:** A pure-Python rule engine checks the case against a registry of eight clinical red-flag rules (chest pain, FAST stroke, anaphylaxis, etc.) and enforces a minimum ESI floor when a rule fires.
- **Layer 3 — RAG Clinical Assessment:** Relevant chunks from ESI protocol documents are retrieved from ChromaDB using semantic search, then passed to GPT-4o-mini to produce an ESI level and routing recommendation grounded in clinical guidance.
- **Layer 4 — Output Verification:** A safety layer enforces the red-flag ESI floor, flags cases requiring human review (ESI ≤ 2 or confidence < 0.7), and returns a validated `TriageOutput`.

---

## Layer 1 — Input Parsing

```python
from src.layers.extraction import extract_patient_case

case = extract_patient_case("55yo male, sudden severe chest pain, 20 min ago")
print(case.model_dump_json(indent=2))
```

---

## Layer 2 — Red-Flag Detection

```python
from src.layers.pipeline import run_intake_pipeline

result = run_intake_pipeline("68yo male, sudden severe chest pain, sweating")
print(result.minimum_esi_floor)  # 1 — forces ESI 1 regardless of what Layer 3 later concludes
```

This layer runs **before** the LLM and establishes a safety floor that Layer 4 (Week 5) will enforce no matter what the LLM outputs in Layer 3. Rules are deterministic, auditable, and require zero API calls.

---

## Tech Stack

| Component | Technology |
|---|---|
| LLM | GPT-4o-mini |
| Embeddings | text-embedding-3-small |
| Vector store | ChromaDB (cosine distance) |
| Data validation | Pydantic v2 |
| UI | Streamlit |
| Container | Docker |

---

## Setup

```bash
git clone <repo-url>
cd patient-triage-assistant

cp .env.example .env
# Add your OPENAI_API_KEY to .env

pip install -r requirements.txt

python scripts/verify_db.py   # confirm ChromaDB is ready
pytest tests/ -v              # run smoke tests
```

---

## Project Status

> **Week 3 complete:** Layer 2 (red-flag rule engine) implemented and tested.
> - 14 red-flag rules covering chest pain, stroke (FAST), respiratory distress, hemorrhage, altered consciousness, anaphylaxis, pediatric fever, severe abdominal pain, hypotension, tachycardia, high fever, suicidal ideation, and pregnancy complications
> - Pure Python, zero LLM dependency — fully deterministic and auditable
> - Every trigger logged to `logs/triage_events.jsonl` for audit trail
> - 16 unit tests, 100% rule coverage, all passing without API calls
> - Layers 1+2 wired together via `run_intake_pipeline()`

---

## Running Tests

```bash
pytest tests/ -m "not integration"     # fast tests only
pytest tests/ -m integration            # integration tests (uses OpenAI API, costs credits)
pytest tests/                           # all tests
```

---

## Disclaimer

This tool is for decision-support only. All assessments must be reviewed and confirmed by qualified clinical staff before any action is taken. It is not a substitute for professional medical judgement.

> Red-flag rules in `src/core/red_flag_rules.py` are illustrative and based on general clinical triage principles (ESI, FAST stroke criteria). They are NOT a substitute for clinically validated protocols and would require review by a licensed clinician before any real-world use.
