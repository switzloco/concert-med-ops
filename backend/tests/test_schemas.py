"""
Unit tests for Pydantic schemas (backend/schemas/pydantic_models.py).

Covers: validation, JSON field parsing, required vs optional fields,
and serialization round-trips.
"""
import json
import pytest
from datetime import datetime, date
from pydantic import ValidationError

from backend.schemas.pydantic_models import (
    EventRead, EventCreate, EventUpdate,
    StaffMemberRead, StaffMemberCreate, StaffMemberUpdate,
    PatientRead, PatientCreate, PatientUpdate,
    EncounterRead, EncounterCreate, EncounterUpdate, VitalSigns,
    ReagentLogRead, ReagentLogCreate,
    SupplyRead, SupplyCreate, SupplyUpdate,
    TriageQueryRequest, TransportDecisionRequest,
)


# ── Event Schemas ────────────────────────────────────────────────────────────

class TestEventSchemas:
    def test_event_create_minimal(self):
        e = EventCreate(name="Griztronics 2026")
        assert e.name == "Griztronics 2026"
        assert e.venue is None

    def test_event_create_missing_name(self):
        with pytest.raises(ValidationError):
            EventCreate()


# ── StaffMember Schemas ──────────────────────────────────────────────────────

class TestStaffMemberSchemas:
    def test_staff_create_minimal(self):
        s = StaffMemberCreate(
            event_id="evt-1",
            name="Alice",
            role="rn",
            call_sign="Med-1",
        )
        assert s.name == "Alice"
        assert s.is_on_shift is True

    def test_staff_create_missing_required(self):
        with pytest.raises(ValidationError):
            StaffMemberCreate(event_id="evt-1")


# ── Patient Schemas ──────────────────────────────────────────────────────────

class TestPatientSchemas:
    def test_patient_create_minimal(self):
        p = PatientCreate(event_id="evt-1", identifier="Red Band #42")
        assert p.identifier == "Red Band #42"
        assert p.location_found == "other"

    def test_patient_read_parses_json_fields(self):
        class FakePatient:
            patient_id = "pat-1"
            event_id = "evt-1"
            identifier = "Band #12"
            approx_age = 22
            gender = "M"
            weight_kg = 75.0
            known_allergies = '["Nuts", "Sulfa"]'
            known_medications = '["Prozac"]'
            known_conditions = '[]'
            substances_reported = '[{"name": "Alcohol", "amount": "3 beers"}]'
            location_found = "campground"
            is_active = True
            created_at = datetime.utcnow()

        p = PatientRead.model_validate(FakePatient())
        assert p.known_allergies == ["Nuts", "Sulfa"]
        assert p.known_medications == ["Prozac"]
        assert len(p.substances_reported) == 1
        assert p.substances_reported[0].name == "Alcohol"


# ── Encounter Schemas ────────────────────────────────────────────────────────

class TestEncounterSchemas:
    def test_encounter_create_with_vitals(self):
        enc = EncounterCreate(
            event_id="evt-1",
            patient_id="pat-1",
            doc_type="pcr",
            logged_by="staff-1",
            vital_signs=VitalSigns(hr=110, bp="130/85", temp_f=101.2),
        )
        assert enc.vital_signs.hr == 110
        assert enc.vital_signs.temp_f == 101.2

    def test_encounter_read_parses_json_fields(self):
        class FakeEncounter:
            encounter_id = "enc-1"
            event_id = "evt-1"
            patient_id = "pat-1"
            doc_type = "pcr"
            logged_by = "staff-1"
            encounter_time = datetime.utcnow()
            chief_complaint = "Panic"
            symptoms = '["anxiety", "chest pain"]'
            vital_signs = '{"hr": 95, "bp": "120/80"}'
            substances_involved = '["cannabis"]'
            triage_level = "yellow"
            escalated_to = None
            escalation_time = None
            interventions = '[{"action": "Reassurance", "by_whom": "Med-1"}]'
            disposition = "released"
            transport_hospital = None
            transport_unit = None
            transport_time = None
            ama_documented = False
            ama_capacity_assessment = None
            ai_response = None
            ai_model_used = None
            photo_paths = "[]"
            notes = "Spoke with peer counselor."
            created_at = datetime.utcnow()

        e = EncounterRead.model_validate(FakeEncounter())
        assert e.symptoms == ["anxiety", "chest pain"]
        assert e.vital_signs["hr"] == 95
        assert len(e.interventions) == 1
        assert e.interventions[0]["action"] == "Reassurance"


# ── ReagentLog Schemas ───────────────────────────────────────────────────────

class TestReagentLogSchemas:
    def test_reagent_create_success(self):
        r = ReagentLogCreate(
            event_id="evt-1",
            patient_id="pat-1",
            sample_description="Yellow powder",
            test_type="marquis",
            test_result="color_change_verified",
            color_observed="purple",
            predicted_substance="MDMA",
            disclaimer_agreed=True,
            tester_staff_id="staff-1",
        )
        assert r.disclaimer_agreed is True

    def test_reagent_create_disclaimer_required(self):
        """Should raise ValidationError if disclaimer_agreed is False."""
        with pytest.raises(ValidationError, match="You must read and agree to the liability disclaimer"):
            ReagentLogCreate(
                event_id="evt-1",
                patient_id="pat-1",
                sample_description="Yellow powder",
                test_type="marquis",
                test_result="color_change_verified",
                color_observed="purple",
                predicted_substance="MDMA",
                disclaimer_agreed=False,
                tester_staff_id="staff-1",
            )


# ── Supply Schemas ───────────────────────────────────────────────────────────

class TestSupplySchemas:
    def test_supply_create(self):
        s = SupplyCreate(
            event_id="evt-1",
            name="IV Normal Saline 1L",
            category="iv_fluid",
            quantity_start=100,
            quantity_remaining=100,
            location="campground",
        )
        assert s.name == "IV Normal Saline 1L"
        assert s.quantity_remaining == 100
