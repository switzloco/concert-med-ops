# Event Med AI

Event Med AI (rebranded from Concert Med Ops) is a clinical decision support and incident tracking tool built for supervising physicians, paramedics, and EMTs working at mass gathering events. 

The primary target environment is a temporary field emergency department embedded inside a large festival, such as **Griztronics 2026 at The Gorge Amphitheatre, WA** (22,500 attendance).

## Key Features

- **ER Whiteboard / Incident Queue**: Dynamic patient list sorting by triage levels with physician-escalation triggers.
- **PCR vs OTC Encounters**: Rapid intake logs for low-acuity cases (OTC handouts) versus full Patient Care Reports (PCR).
- **AMA Refusal Assessment**: Structured Capacity Assessment for Patients wishing to leave against medical advice.
- **Drug Checking / Reagent Log**: presubstance identification logs with Marquis/Mecke visual confirmation and strict legal disclaimers.
- **AI Decision Support**: Local Ollama or Gemini Cloud fallback guiding clinicians through heat index alerts, transport drive-times, and rave polydrug interaction guidelines.

## Architecture

- **Backend**: FastAPI + SQLite WAL + SQLAlchemy
- **Frontend**: Next.js 14 + Tailwind CSS
- **Desktop Wrapper**: Tauri 2 (rust-based desktop container)
- **AI Engine**: Local Ollama (Gemma 4) with direct Gemini Cloud API fallback
- **RAG Engine**: SQLite FTS5 for fast BM25 search over local harm reduction protocols

## Setup & Running

See backend configuration in `.env`. Run local servers:

```bash
# Start backend
uv run python backend/main.py

# Start frontend
cd frontend
npm run dev
```
