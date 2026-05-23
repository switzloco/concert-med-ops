"""
Integration and walkthrough tests for Event Med AI complex endpoints.

Covers: Setup status checks under cloud/local mode, API workflows,
and AI prompt templates integration (triage, transport decision, etc.)
with mock LLM and RAG engines.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from backend.config import settings

class TestWalkthroughLogic:
    @patch("backend.routers.setup._is_ollama_installed", return_value=False)
    @patch("backend.routers.setup._check_ollama_running", new_callable=AsyncMock, return_value=False)
    @patch("backend.routers.setup._check_model_ready", new_callable=AsyncMock, return_value=False)
    def test_setup_status_ollama_not_installed(self, mock_ready, mock_running, mock_installed, client):
        r = client.get("/api/setup/status")
        assert r.status_code == 200
        data = r.json()
        assert data["ollama_installed"] is False
        assert data["ollama_running"] is False
        assert data["model_ready"] is False

    @patch("backend.routers.setup._is_ollama_installed", return_value=True)
    @patch("backend.routers.setup._check_ollama_running", new_callable=AsyncMock, return_value=True)
    @patch("backend.routers.setup._check_model_ready", new_callable=AsyncMock, return_value=False)
    def test_setup_status_ollama_running_no_model(self, mock_ready, mock_running, mock_installed, client):
        r = client.get("/api/setup/status")
        assert r.status_code == 200
        data = r.json()
        assert data["ollama_installed"] is True
        assert data["ollama_running"] is True
        assert data["model_ready"] is False

    @patch("backend.routers.setup._is_ollama_installed", return_value=False)
    @patch("backend.routers.setup._check_ollama_running", new_callable=AsyncMock, return_value=False)
    @patch("backend.routers.setup._check_model_ready", new_callable=AsyncMock, return_value=False)
    def test_setup_status_cloud_mode_bypasses_ollama_checks(self, mock_ready, mock_running, mock_installed, client):
        # In cloud mode the app uses Gemini, not Ollama, so the status endpoint
        # short-circuits all Ollama checks and reports the app ready.
        client.post("/api/setup/mode", json={"mode": "cloud"})

        r = client.get("/api/setup/status")
        assert r.status_code == 200
        data = r.json()
        assert data["mode"] == "cloud"
        assert data["ollama_installed"] is True
        assert data["ollama_running"] is True
        assert data["model_ready"] is True

        client.post("/api/setup/mode", json={"mode": "local"})

    def test_event_info_cycle(self, client):
        # Initial get should create default
        r = client.get("/api/setup/event-info")
        assert r.status_code == 200
        assert r.json()["name"] == "Griztronics 2026"
        
        # Update it
        r = client.post("/api/setup/event-info", json={"name": "Antigravity Event", "venue": "The Gorge, WA"})
        assert r.status_code == 200
        assert r.json()["name"] == "Antigravity Event"
        assert r.json()["venue"] == "The Gorge, WA"
        
        # Verify it persisted
        r = client.get("/api/setup/event-info")
        assert r.json()["name"] == "Antigravity Event"


class TestAIResponseQuality:
    @patch("backend.routers.ai._llm_tokens")
    @patch("backend.routers.ai.get_rag_engine")
    def test_triage_query_prompt_construction(self, mock_rag, mock_llm, client, seed_patient):
        # Mock RAG to return nothing
        mock_rag.return_value.hybrid_query.return_value = []
        
        # Mock LLM to yield a single token
        async def mock_iter(*args, **kwargs):
            yield "Test response"
        mock_llm.side_effect = mock_iter
        
        payload = {
            "patient_id": seed_patient.patient_id,
            "current_symptoms": ["muscle rigidity", "hyperthermia"],
            "vitals": {"bp": "150/100", "hr": 130, "temp_f": 104.2, "gcs": 13},
            "notes": "Suspected serotonin syndrome"
        }
        
        # We use a stream, so we need to iterate it
        with client.stream("POST", "/api/ai/triage-query", json=payload) as r:
            assert r.status_code == 200
            saw_token = False
            for line in r.iter_lines():
                if "token" in line:
                    saw_token = True
                    break
            assert saw_token, "expected at least one token event in stream"
            
        # Verify the prompt construction (internal check of call args)
        call_args = mock_llm.call_args
        system_prompt = call_args[0][0]
        user_prompt = call_args[0][1]
        
        assert "mass gathering EDM festival" in system_prompt
        assert "Patient ID (Wristband/Desc): Red Band #42" in user_prompt
        assert "muscle rigidity, hyperthermia" in user_prompt
        assert "Temp=104.2" in user_prompt
        assert "Event Med AI" in system_prompt

    @patch("backend.routers.ai._llm_tokens")
    @patch("backend.routers.ai.get_rag_engine")
    def test_triage_query_with_rag(self, mock_rag, mock_llm, client, seed_patient):
        # Mock RAG to return protocols
        mock_rag.return_value.hybrid_query.return_value = [
            {"text": "Apply active cooling immediately for heat stroke.", "metadata": {"title": "Hyperthermia Protocol"}}
        ]
        
        async def mock_iter(*args, **kwargs):
            yield "Response"
        mock_llm.side_effect = mock_iter
        
        payload = {
            "patient_id": seed_patient.patient_id,
            "current_symptoms": ["heat stroke"],
            "severity": "critical"
        }
        
        with client.stream("POST", "/api/ai/triage-query", json=payload) as r:
            assert r.status_code == 200
            
        user_prompt = mock_llm.call_args[0][1]
        assert "Relevant Protocol Excerpts:" in user_prompt
        assert "Apply active cooling" in user_prompt
        assert "Source: Hyperthermia Protocol" in user_prompt
