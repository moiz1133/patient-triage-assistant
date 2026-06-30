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

> **Week 1 complete:** project scaffold, Pydantic schemas, ChromaDB client, red-flag rule registry, and smoke tests.

---

## Disclaimer

This tool is for decision-support only. All assessments must be reviewed and confirmed by qualified clinical staff before any action is taken. It is not a substitute for professional medical judgement.
