# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This App Is

**Event Med AI** — an offline-capable clinical decision support and incident tracking tool for supervising physicians, paramedics, and EMTs working mass-gathering medical operations (target: Griztronics 2026, The Gorge Amphitheatre, WA, 22,500 attendees). Primary presentation types are MDMA/stimulant toxicity, hyperthermia, hyponatremia, GHB overdose, polysubstance interactions, and serotonin syndrome.

## Commands

### Backend

```bash
# Run backend (from repo root)
uv run python backend/main.py
# or
uvicorn backend.main:app --reload --port 8000

# Run all tests
python -m pytest

# Run a single test file
python -m pytest backend/tests/test_rag_engine.py -v

# Run a single test class or function
python -m pytest backend/tests/test_api.py::TestPatientRouter::test_list_patients_empty -v

# Seed the RAG knowledge base (run once, or after clearing knowledge.sqlite)
python -m backend.data.seed_knowledge

# Ingest full Tier-1 PDF corpus (requires internet + manual PDF downloads for 403-blocked sources)
python -m backend.scripts.ingest_rag_sources --tier 1

# Ingest a single source with a manually downloaded PDF
python -m backend.scripts.ingest_rag_sources --source who_mass_gatherings \
    --local-pdf ~/Downloads/WHO_HSE_GCR_2015.5_eng.pdf

# Dry-run to inspect chunk sizes without writing to DB
python -m backend.scripts.ingest_rag_sources --dry-run
```

### Frontend

```bash
cd frontend
npm run dev          # Next.js dev server on :3000
npm run build        # Static export to frontend_out/
npm run lint
npm run tauri:dev    # Tauri desktop wrapper (requires Rust toolchain)
```

### Environment

Copy `.env.example` to `.env`. Key vars:
- `CLOUD_MODE=true` + `GEMINI_API_KEY=...` — routes all LLM calls to Gemini 2.5 Flash instead of local Ollama
- `MODEL_MEDICAL=concert-med-tox` — activates the Unsloth fine-tuned model if installed via Ollama
- `EVENT_MED_DATA_DIR` — overrides where both SQLite databases (`event_med.db` and `knowledge.sqlite`) are written

## Architecture

### Two Separate SQLite Databases

1. **`event_med.db`** — SQLAlchemy-managed operational DB. All patient, encounter, incident, staff, supply, reagent, and hospital records. WAL mode, foreign keys on. Schema defined in `backend/db/models.py`.

2. **`knowledge.sqlite`** — RAG index. SQLite FTS5 virtual table (`rag_chunks`) with porter tokenizer. Managed exclusively by `backend/ai/rag_engine.py`. Never touched by SQLAlchemy. Schema version tracked in `_schema_meta` table (currently v2, which added `drugs_tagged` and `condition_tags` FTS5 columns).

### LLM Routing

`backend/ai/mode_state.py` holds a runtime toggle (`cloud`/`local`). On every request, `backend/routers/ai.py::_llm_tokens()` checks `mode_state.is_cloud()` and dispatches to either:
- `backend/ai/google_client.py` — streams from Gemini API via `google-genai`
- `backend/ai/ollama_client.py` — `OllamaRouter` picks between `model_primary` (default) and `model_scale` (heavier model triggered when temp ≥ 104°F or GCS ≤ 9)

The fine-tuned Unsloth model (`settings.effective_medical_model`) is a third Ollama model slot activated via `MODEL_MEDICAL=` env var.

### RAG Engine — Hybrid Retrieval

`backend/ai/rag_engine.py::hybrid_query()` does two-stage retrieval:
1. **BM25** via FTS5 MATCH on all columns (text, drugs_tagged, condition_tags), k×2 candidates
2. **Drug-name exact-match boost**: re-queries `drugs_tagged` column for each named substance, moves matching chunks to top of results
3. **Token budget**: enforces `max_context_tokens=3000` (≈ words × 1.3), always returns ≥1 result

`add_documents()` stores `drugs_tagged` and `condition_tags` as space-separated strings for FTS5 indexing. All metadata (including `page_start`, `page_end` for PDFs and `section` for HTML) is serialized as JSON in the `metadata` column.

### Citation Format

`backend/routers/ai.py::_format_citation()` builds citation strings from chunk metadata:
- PDF chunks: `"SAMHSA Toolkit, pp. 12–14 [url]"`
- HTML chunks: `"EMCrit IBCC — Cooling Protocol [url]"`
- No page/section: `"Title [url]"`

### RAG Knowledge Base Bootstrap

On `RAGEngine.__init__()`, if `knowledge.sqlite` is empty:
1. Loads `backend/data/harm_reduction_kb.json` (small legacy seed, 11 chunks)
2. Calls `backend/data/seed_knowledge.py::seed_knowledge_base(engine=self)` — 24 clinically authoritative chunks covering naloxone protocol, heat stroke cooling, EAH/hyponatremia (WMS 2020), GHB intoxication, serotonin syndrome (Hunter criteria), chemical sedation (ACEP 2021), START/SALT triage, and polysubstance interactions

**To populate with full authoritative PDFs:** Run `python -m backend.scripts.ingest_rag_sources` after manually downloading sources that block automated fetching (all Tier-1 PDFs return 403 from automated requests). Download each PDF manually and re-run with `--local-pdf`. Sources and their keys are listed in `backend/data/sources/SOURCES.md`.

### Ingestion Pipeline (`backend/scripts/ingest_rag_sources.py`)

- **PDF path**: `_extract_pdf_pages()` (PyMuPDF) → `chunk_paged_text()` → stores `page_start`/`page_end` per chunk
- **HTML path**: `_fetch_html_sections()` (trafilatura, splits on Markdown `#`/`##`/`###` headings) → `chunk_html_section()` → stores `section` heading per chunk
- Each chunk is auto-tagged by `_tag_chunk()` using keyword taxonomies in `CONDITION_KEYWORDS` and `DRUG_KEYWORDS` dictionaries, merged with doc-level `condition_hints`/`drug_hints`
- Chunk target: ~423 words (≈550 tokens), min 307, max 538, 76-word overlap

### API Endpoints

All routes under `/api/`:
- `/api/ai/*` — AI assistant endpoints (triage-query, transport-decision, drug-interaction, chat, extract-encounter-info, knowledge-stats)
- `/api/patient`, `/api/encounter`, `/api/reagent`, `/api/tracking`, `/api/hospitals`, `/api/staff`, `/api/supplies`, `/api/setup`, `/api/uploads`
- All AI endpoints return `text/event-stream` SSE for streaming tokens, except `/knowledge-stats` and `/extract-encounter-info`

### Frontend Pages

Next.js 14 App Router. Pages in `frontend/src/app/`:
- `/board` — ER whiteboard / incident queue (primary clinical view)
- `/patients` — patient list and intake
- `/encounter` — PCR/OTC encounter form with AI triage button
- `/reagent` — drug checking / reagent log
- `/chat` — conversational AI assistant
- `/settings` — cloud/local mode toggle, Ollama config

`SetupGate` component (`frontend/src/components/setup/SetupGate.tsx`) gates the app behind event creation on first run.

### Tests

Tests use an isolated `test_event_med.db` file (not in-memory, to support WAL mode). `conftest.py` overrides `DATABASE_URL` and `get_db` before any imports. `test_rag_engine.py` uses `EVENT_MED_DATA_DIR` pointed at a `tempfile.mkdtemp()` and patches `_BUNDLED_KB_PATH` to skip bootstrap.

The AI router tests mock Ollama; `CLOUD_MODE=false` + `GOOGLE_API_KEY=test-key-not-real` are set in conftest before imports.

### Prompt System

`backend/ai/prompt_templates.py` contains `TRIAGE_SYSTEM`, `TRANSPORT_DECISION_SYSTEM`, `DRUG_INTERACTION_SYSTEM`, `GENERAL_SYSTEM`. The transport system prompt hard-codes the four real hospitals near The Gorge (Quincy Valley, Samaritan Moses Lake, Central Washington Wenatchee, Harborview Seattle) with their drive times and trauma levels — update these if the event venue changes.

`CITATION_INSTRUCTIONS` is appended to the system prompt only when RAG results are available. `SUCCINCT_MODIFIER` is always appended to keep responses actionable in a loud field environment.

### Key Constraints

- **Token cap**: 3,000 tokens total RAG context per query — Gemma 3 4B degrades on longer context
- **Model scaling**: Red/Black triage patients auto-escalate to `model_scale` (heavier Ollama model)
- **Fine-tune dataset target**: 1,500–2,500 ShareGPT pairs — exceeding ~2,500 causes knowledge forgetting in small models. See `notebooks/generate_training_data.py` and `notebooks/unsloth_finetune.ipynb`
- **Chunk IDs are stable**: `_chunk_id()` is keyed on source key + index + hash of first 64 chars — re-ingesting a source is idempotent via DELETE+INSERT
- **Patient privacy**: `identifier` field stores wristband number or physical description, never legal name
- **ReagentLog**: requires `disclaimer_agreed=True` at the DB constraint level; the validation exception handler in `main.py` surfaces a human-readable error for this specific field
