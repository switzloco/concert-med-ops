import asyncio
import json
import re
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import AsyncIterator, List, Optional, Dict, Any

from backend.ai import mode_state
from backend.config import settings
from backend.db.database import get_db
from backend.db.models import Patient, HospitalDirectory, Encounter
from backend.schemas.pydantic_models import (
    TriageQueryRequest, TransportDecisionRequest,
    DrugInteractionQueryRequest, ExtractEncounterRequest
)
from backend.ai.prompt_templates import (
    TRIAGE_SYSTEM, TRANSPORT_DECISION_SYSTEM,
    DRUG_INTERACTION_SYSTEM, GENERAL_SYSTEM,
    DISCLAIMER, SUCCINCT_MODIFIER, CITATION_INSTRUCTIONS
)

_rag_engine = None


def _format_citation(meta: dict) -> str:
    """Build a readable citation string including page or section when available."""
    title = meta.get("title", "Reference")
    source_url = meta.get("source_url", "")
    page_start = meta.get("page_start")
    page_end = meta.get("page_end")
    section = meta.get("section")

    cite = title
    if page_start is not None:
        if page_end and page_end != page_start:
            cite += f", pp. {page_start}–{page_end}"
        else:
            cite += f", p. {page_start}"
    elif section:
        cite += f" — {section}"
    if source_url:
        cite += f" [{source_url}]"
    return cite


def get_rag_engine():
    global _rag_engine
    if _rag_engine is None:
        from backend.ai.rag_engine import RAGEngine
        _rag_engine = RAGEngine()
    return _rag_engine

router = APIRouter()


@router.get("/knowledge-stats")
def get_knowledge_stats():
    engine = get_rag_engine()
    stats = engine.all_collection_stats()
    # Always surface the core collections even if empty
    for col in ("harm_reduction_protocols", "substance_database", "mass_gathering_protocols"):
        stats.setdefault(col, 0)
    return stats


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    patient_id: Optional[str] = None
    succinct: bool = True


async def _tokens_to_sse(token_iter: AsyncIterator[str], model_label: Optional[str] = None):
    if model_label:
        yield f"data: {json.dumps({'model': model_label})}\n\n"
    async for token in token_iter:
        yield f"data: {json.dumps({'token': token})}\n\n"
    yield f"data: {json.dumps({'done': True})}\n\n"


def _model_label(model_override: Optional[str]) -> str:
    if mode_state.is_cloud():
        return f"Gemini Cloud ({settings.cloud_model})"
    if model_override and model_override != settings.model_primary:
        return f"Local Ollama (Scale: {model_override})"
    return f"Local Ollama (Primary: {settings.model_primary})"


async def _llm_tokens(
    system: str,
    user_prompt: str,
    images: Optional[List[bytes]] = None,
    triage_level: str = "green",
    model_override: Optional[str] = None,
) -> AsyncIterator[str]:
    """Route LLM generation to cloud or local based on runtime config."""
    if mode_state.is_cloud():
        from backend.ai.google_client import GoogleClient
        client = GoogleClient(
            api_key=settings.google_api_key,
            model=settings.cloud_model,
        )
        async for token in client.chat_stream(system, user_prompt, images=images):
            yield token
    else:
        from backend.ai.ollama_client import OllamaRouter
        router = OllamaRouter(
            host=settings.ollama_host,
            model_primary=settings.model_primary,
            model_scale=settings.model_scale,
        )
        async for token in router.chat_stream(
            system,
            user_prompt,
            triage_level=triage_level,
            images=images,
            model_override=model_override,
        ):
            yield token


async def _llm_full_response(system: str, user_prompt: str) -> str:
    full_text = ""
    async for token in _llm_tokens(system, user_prompt):
        full_text += token
    return full_text


@router.post("/triage-query")
async def triage_query(payload: TriageQueryRequest, db: Session = Depends(get_db)):
    """Evaluate patient presenting symptoms & vitals, referencing protocols."""
    patient = db.query(Patient).filter(Patient.patient_id == payload.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    reported_substances = json.loads(patient.substances_reported or "[]")
    
    user_prompt = (
        f"Patient ID (Wristband/Desc): {patient.identifier}\n"
        f"Approximate Age: {patient.approx_age or 'Unknown'}\n"
        f"Gender: {patient.gender or 'Unknown'}\n"
        f"Chief Symptoms Reported: {', '.join(payload.current_symptoms)}\n"
    )
    
    if payload.vitals:
        v = payload.vitals
        user_prompt += (
            f"Current Vitals: HR={v.hr or '?'}, BP={v.bp or '?'}, Temp={v.temp_f or '?'}°F, "
            f"SpO2={v.spo2 or '?'}%, RR={v.rr or '?'}, GCS={v.gcs or '?'}, Pupils={v.pupils or '?'}, Skin={v.skin_condition or '?'}\n"
        )

    if reported_substances:
        user_prompt += "Reported Substances Intake:\n"
        for sub in reported_substances:
            user_prompt += f"- {sub.get('name')} (amount: {sub.get('amount')}, route: {sub.get('route')}, time: {sub.get('time_taken')})\n"
            
    if payload.notes:
        user_prompt += f"Clinical Notes: {payload.notes}\n"

    # Hybrid RAG: BM25 on symptoms + exact-match boost on substance names
    query_terms = " ".join(payload.current_symptoms)
    if payload.notes:
        query_terms += " " + payload.notes
    drug_names = [s.get("name", "") for s in reported_substances if s.get("name")]

    rag_engine = get_rag_engine()
    # Search across both clinical protocols and mass gathering ops collections
    rag_results = rag_engine.hybrid_query(
        "harm_reduction_protocols", query_terms, drug_names=drug_names or None, k=5
    )
    rag_results += rag_engine.hybrid_query(
        "mass_gathering_protocols", query_terms, drug_names=drug_names or None, k=2
    )

    has_rag = False
    if rag_results:
        has_rag = True
        user_prompt += "\nRelevant Protocol Excerpts:\n"
        for r in rag_results:
            cite = _format_citation(r['metadata'])
            user_prompt += f"- {r['text']} (Source: {cite})\n"

    system = TRIAGE_SYSTEM
    if has_rag:
        system += CITATION_INSTRUCTIONS
    system += SUCCINCT_MODIFIER

    # Pick scale model override if triage vitals represent severe issues (e.g. Temp > 104, GCS < 9)
    model_override = None
    triage_lvl = "green"
    if payload.vitals:
        temp = payload.vitals.temp_f or 98.6
        gcs = payload.vitals.gcs or 15
        if temp >= 104.0 or gcs <= 9:
            triage_lvl = "red"
            model_override = settings.model_scale

    return StreamingResponse(
        _tokens_to_sse(
            _llm_tokens(system, user_prompt, triage_level=triage_lvl, model_override=model_override),
            model_label=_model_label(model_override)
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/transport-decision")
async def transport_decision(payload: TransportDecisionRequest, db: Session = Depends(get_db)):
    """Evaluate whether to transport a patient or treat on-site based on hospital diversion & capabilities."""
    patient = db.query(Patient).filter(Patient.patient_id == payload.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    hospitals = db.query(HospitalDirectory).all()
    hospitals_str = "Available Hospitals & Stats:\n"
    for h in hospitals:
        capabilities = json.loads(h.capabilities or "[]")
        h_status = "DIVERSION ACTIVE" if h.is_on_diversion else "OPEN"
        hospitals_str += (
            f"- {h.name}: Drive time={h.drive_time_min} mins, Distance={h.distance_miles} miles, "
            f"Trauma Level={h.trauma_level or 'None'}, Capabilities={', '.join(capabilities)}, "
            f"Status={h_status}, Notes={h.notes or 'None'}\n"
        )

    user_prompt = (
        f"Patient ID: {patient.identifier}\n"
        f"Triage Level: {payload.triage_level.upper()}\n"
        f"Chief Complaints: {', '.join(payload.current_symptoms)}\n"
    )

    if payload.vitals:
        v = payload.vitals
        user_prompt += (
            f"Vitals: HR={v.hr or '?'}, BP={v.bp or '?'}, Temp={v.temp_f or '?'}°F, "
            f"SpO2={v.spo2 or '?'}%, RR={v.rr or '?'}, GCS={v.gcs or '?'}, Pupils={v.pupils or '?'}\n"
        )
        
    user_prompt += f"\n{hospitals_str}\n"
    user_prompt += f"Ambulance Resource Status: {payload.ambulance_status or 'Standard deployment (high threshold)'}\n"
    if payload.notes:
        user_prompt += f"Additional Notes: {payload.notes}\n"

    # Query transport/triage from RAG
    rag_engine = get_rag_engine()
    transport_query = f"hospital transport triage {' '.join(payload.current_symptoms)}"
    rag_results = rag_engine.hybrid_query("mass_gathering_protocols", transport_query, k=2)
    rag_results += rag_engine.hybrid_query("harm_reduction_protocols", "AMA Refusal Capacity Checklist", k=1)
    if rag_results:
        user_prompt += "\nRelevant Protocol Excerpts:\n"
        for r in rag_results:
            cite = _format_citation(r['metadata'])
            user_prompt += f"- {r['text']} (Source: {cite})\n"

    system = TRANSPORT_DECISION_SYSTEM
    system += SUCCINCT_MODIFIER

    model_override = settings.model_scale if payload.triage_level in ("red", "black") else None

    return StreamingResponse(
        _tokens_to_sse(
            _llm_tokens(system, user_prompt, triage_level=payload.triage_level, model_override=model_override),
            model_label=_model_label(model_override)
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/drug-interaction")
async def drug_interaction(payload: DrugInteractionQueryRequest):
    """Scan multi-substance interactions and output warning signs & protocols."""
    if not payload.substances:
        raise HTTPException(status_code=400, detail="No substances provided for interaction checking")

    user_prompt = f"Evaluate interactions between these substances: {', '.join(payload.substances)}\n"
    
    # Hybrid query: drug-name exact-match boost across both collections
    rag_engine = get_rag_engine()
    drug_names = [s.strip().lower() for s in payload.substances]
    interaction_query = " ".join(payload.substances) + " interaction toxicity"

    rag_results = rag_engine.hybrid_query(
        "harm_reduction_protocols", interaction_query, drug_names=drug_names, k=5
    )
    rag_results += rag_engine.hybrid_query(
        "substance_database", interaction_query, drug_names=drug_names, k=2
    )

    if rag_results:
        user_prompt += "\nRelevant Clinical References:\n"
        for r in rag_results:
            cite = _format_citation(r['metadata'])
            user_prompt += f"- {r['text']} (Source: {cite})\n"

    system = DRUG_INTERACTION_SYSTEM
    system += SUCCINCT_MODIFIER

    return StreamingResponse(
        _tokens_to_sse(
            _llm_tokens(system, user_prompt),
            model_label=_model_label(None)
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/chat")
async def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    """Conversational assistant for medical staff, optionally grounded in active patient file."""
    context_lines = []
    system = GENERAL_SYSTEM

    if payload.patient_id:
        patient = db.query(Patient).filter(Patient.patient_id == payload.patient_id).first()
        if patient:
            context_lines.append(f"Active Patient under discussion: Wristband/ID={patient.identifier}")
            context_lines.append(f"  Approx Age={patient.approx_age or '?'}, Gender={patient.gender or '?'}")
            
            substances = json.loads(patient.substances_reported or "[]")
            if substances:
                subs_str = ", ".join([f"{s.get('name')} ({s.get('amount') or '?'})" for s in substances])
                context_lines.append(f"  Reported Substances: {subs_str}")

            # Grab recent encounters for context
            encounters = db.query(Encounter).filter(Encounter.patient_id == patient.patient_id).order_by(Encounter.encounter_time.desc()).limit(2).all()
            if encounters:
                context_lines.append("  Recent Encounters:")
                for enc in encounters:
                    context_lines.append(
                        f"    - Type={enc.doc_type.upper()}, Complaint={enc.chief_complaint or 'None'}, Triage={enc.triage_level.upper()}, Disposition={enc.disposition}"
                    )

    # Hybrid RAG on last message across all collections
    last_msg = payload.messages[-1].content
    rag_engine = get_rag_engine()
    protocols_rag = rag_engine.hybrid_query("harm_reduction_protocols", last_msg, k=3)
    substance_rag = rag_engine.hybrid_query("substance_database", last_msg, k=1)
    mass_rag = rag_engine.hybrid_query("mass_gathering_protocols", last_msg, k=1)

    has_rag = False
    if protocols_rag or substance_rag or mass_rag:
        has_rag = True
        context_lines.append("\nRelevant Clinical Guidelines:")
        for r in (protocols_rag + substance_rag + mass_rag):
            cite = _format_citation(r['metadata'])
            context_lines.append(f"- {r['text']} (Source: {cite})")

    if context_lines:
        system += "\n\nContext for this session:\n" + "\n".join(context_lines)

    if has_rag:
        system += CITATION_INSTRUCTIONS

    if payload.succinct:
        system += SUCCINCT_MODIFIER

    transcript = "\n\n".join(
        f"{'User' if m.role == 'user' else 'Assistant'}: {m.content}"
        for m in payload.messages
    )
    transcript += "\n\nAssistant:"

    return StreamingResponse(
        _tokens_to_sse(
            _llm_tokens(system, transcript),
            model_label=_model_label(None)
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/extract-encounter-info")
async def extract_encounter_info(payload: ExtractEncounterRequest):
    """Analyze verbal/written transcript to extract vitals, symptoms, and severity."""
    system = "You are a clinical documentation assistant for a festival medical tent. Extract symptoms, severity, and vitals into a structured JSON object."
    user_prompt = f"""Analyze the following clinical intake description:
"{payload.text}"

Return ONLY a JSON object with these exact keys. Do not include markdown code block formatting (e.g. do not wrap in ```json).
- symptoms (list of strings)
- hr (integer or null)
- bp (string or null)
- temp_f (float or null)
- spo2 (integer or null)
- rr (integer or null)
- gcs (integer or null)
- triage_level (one of: green, yellow, red, black)
- disposition (one of: released, observation, transport, ama)
- substances_involved (list of strings)
- chief_complaint (string or null)
"""
    response_text = await _llm_full_response(system, user_prompt)
    
    # Extract JSON block
    try:
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group(0))
            return parsed
    except Exception:
        pass
        
    return {
        "raw_response": response_text,
        "symptoms": [],
        "vital_signs": {},
        "triage_level": "green"
    }
