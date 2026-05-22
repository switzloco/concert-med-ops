"""
Unit tests for AI subsystem modules.

Covers: mode_state, prompt_templates, OllamaRouter model selection, and Config.
"""
import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


# ── mode_state ───────────────────────────────────────────────────────────────

class TestModeState:
    def test_get_mode_returns_string(self):
        from backend.ai import mode_state
        mode = mode_state.get_mode()
        assert mode in ("cloud", "local")

    def test_set_mode_local(self):
        from backend.ai import mode_state
        original = mode_state.get_mode()
        try:
            mode_state.set_mode("local")
            assert mode_state.get_mode() == "local"
            assert mode_state.is_cloud() is False
        finally:
            mode_state.set_mode(original)

    def test_set_mode_cloud(self):
        from backend.ai import mode_state
        original = mode_state.get_mode()
        try:
            mode_state.set_mode("cloud")
            assert mode_state.get_mode() == "cloud"
            assert mode_state.is_cloud() is True
        finally:
            mode_state.set_mode(original)

    def test_set_mode_invalid(self):
        from backend.ai import mode_state
        with pytest.raises(ValueError, match="Invalid mode"):
            mode_state.set_mode("quantum")


# ── prompt_templates ─────────────────────────────────────────────────────────

class TestPromptTemplates:
    def test_disclaimer_present(self):
        from backend.ai.prompt_templates import DISCLAIMER
        assert "Event Med AI" in DISCLAIMER
        assert "physician" in DISCLAIMER.lower()

    def test_medical_system_mentions_griztronics(self):
        from backend.ai.prompt_templates import GENERAL_SYSTEM
        assert "Griztronics" in GENERAL_SYSTEM

    def test_triage_system_mentions_serotonin(self):
        from backend.ai.prompt_templates import TRIAGE_SYSTEM
        assert "serotonin" in TRIAGE_SYSTEM.lower()

    def test_transport_system_mentions_gorge(self):
        from backend.ai.prompt_templates import TRANSPORT_DECISION_SYSTEM
        assert "Gorge" in TRANSPORT_DECISION_SYSTEM
        assert "Samaritan" in TRANSPORT_DECISION_SYSTEM

    def test_drug_interaction_system_mentions_ssri(self):
        from backend.ai.prompt_templates import DRUG_INTERACTION_SYSTEM
        assert "SSRI" in DRUG_INTERACTION_SYSTEM


# ── OllamaRouter ────────────────────────────────────────────────────────────

class TestOllamaRouter:
    def test_pick_model_minor(self):
        from backend.ai.ollama_client import OllamaRouter
        router = OllamaRouter(
            host="http://localhost:11434",
            model_primary="gemma4:e2b",
            model_scale="gemma4:e4b",
        )
        assert router._pick_model("green") == "gemma4:e2b"
        assert router._pick_model("yellow") == "gemma4:e2b"

    def test_pick_model_critical(self):
        from backend.ai.ollama_client import OllamaRouter
        router = OllamaRouter(
            host="http://localhost:11434",
            model_primary="gemma4:e2b",
            model_scale="gemma4:e4b",
        )
        assert router._pick_model("red") == "gemma4:e4b"
        assert router._pick_model("black") == "gemma4:e4b"
        assert router._pick_model("critical") == "gemma4:e4b"


# ── Config ───────────────────────────────────────────────────────────────────

class TestConfig:
    def test_cors_origins_from_string(self):
        from backend.config import Settings
        s = Settings(cors_origins="http://a.com, http://b.com")
        assert s.cors_origins == ["http://a.com", "http://b.com"]

    def test_cors_origins_from_list(self):
        from backend.config import Settings
        s = Settings(cors_origins=["http://a.com"])
        assert s.cors_origins == ["http://a.com"]

    def test_default_database_url(self):
        from backend.config import Settings
        s = Settings()
        assert "sqlite" in s.database_url
