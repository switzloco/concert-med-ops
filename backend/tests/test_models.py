"""
Unit tests for SQLAlchemy ORM models (backend/db/models.py).

Covers: table creation, relationships, constraints, defaults, and FK integrity.
"""
import json
import uuid
import pytest
from datetime import datetime, date
from sqlalchemy.exc import IntegrityError

from backend.db.models import (
    Event, StaffMember, Patient, Encounter, IncidentQueue,
    HospitalDirectory, ReagentLog, Supply, _uuid,
)


# ── UUID helper ──────────────────────────────────────────────────────────────

class TestUUIDHelper:
    def test_uuid_returns_string(self):
        result = _uuid()
        assert isinstance(result, str)

    def test_uuid_is_valid_v4(self):
        result = _uuid()
        parsed = uuid.UUID(result)
        assert parsed.version == 4

    def test_uuid_uniqueness(self):
        ids = {_uuid() for _ in range(100)}
        assert len(ids) == 100, "UUIDs should be unique"


# ── Event ────────────────────────────────────────────────────────────────────

class TestEventModel:
    def test_create_event(self, db, seed_event):
        event = db.query(Event).filter(Event.event_id == "test-event-1").first()
        assert event is not None
        assert event.name == "Griztronics 2026"
        assert event.venue == "The Gorge Amphitheatre"

    def test_event_created_at_default(self, db, seed_event):
        assert seed_event.created_at is not None
        assert isinstance(seed_event.created_at, datetime)

    def test_event_relationships(self, db, seed_event, seed_staff, seed_patient, seed_encounter, seed_reagent_log, seed_supply):
        event = db.query(Event).filter(Event.event_id == seed_event.event_id).first()
        assert len(event.staff_members) == 3
        assert len(event.patients) == 1
        assert len(event.encounters) == 1
        assert len(event.reagent_logs) == 1
        assert len(event.supplies) == 1


# ── StaffMember ──────────────────────────────────────────────────────────────

class TestStaffMemberModel:
    def test_create_staff_member(self, db, seed_staff):
        member = db.query(StaffMember).filter(StaffMember.staff_id == "staff-1").first()
        assert member.name == "Alice RN"
        assert member.role == "rn"
        assert member.call_sign == "Med-1"

    def test_staff_member_role_constraint(self, db, seed_event):
        """Role must be one of the allowed values."""
        bad_member = StaffMember(
            staff_id="staff-bad",
            event_id=seed_event.event_id,
            name="Ghost Staff",
            role="wizard",  # not allowed
            call_sign="Med-99",
        )
        db.add(bad_member)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_staff_member_valid_roles(self, db, seed_event):
        roles = ["emt", "paramedic", "rn", "md", "supervisor"]
        for idx, role in enumerate(roles):
            member = StaffMember(
                staff_id=f"staff-role-{idx}",
                event_id=seed_event.event_id,
                name=f"Staff {role}",
                role=role,
                call_sign=f"Med-{idx}",
            )
            db.add(member)
        db.commit()  # should not raise


# ── Patient ──────────────────────────────────────────────────────────────────

class TestPatientModel:
    def test_create_patient(self, db, seed_patient):
        patient = db.query(Patient).filter(Patient.patient_id == "patient-1").first()
        assert patient.identifier == "Red Band #42"
        assert patient.approx_age == 24
        assert patient.location_found == "venue_tent"

    def test_patient_location_constraint(self, db, seed_event):
        bad_patient = Patient(
            patient_id="patient-bad",
            event_id=seed_event.event_id,
            identifier="Bad Patient",
            location_found="space_station",  # not allowed
        )
        db.add(bad_patient)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_patient_valid_locations(self, db, seed_event):
        locations = ["venue_tent", "campground", "gate", "field", "other"]
        for idx, loc in enumerate(locations):
            patient = Patient(
                patient_id=f"patient-loc-{idx}",
                event_id=seed_event.event_id,
                identifier=f"Patient at {loc}",
                location_found=loc,
            )
            db.add(patient)
        db.commit()  # should not raise


# ── Encounter ────────────────────────────────────────────────────────────────

class TestEncounterModel:
    def test_create_encounter(self, db, seed_encounter):
        enc = db.query(Encounter).filter(Encounter.encounter_id == "enc-1").first()
        assert enc.doc_type == "pcr"
        assert enc.chief_complaint == "Palpitations and anxiety"
        vitals = json.loads(enc.vital_signs)
        assert vitals["hr"] == 115

    def test_encounter_doc_type_constraint(self, db, seed_event, seed_patient, seed_staff):
        bad_enc = Encounter(
            encounter_id="enc-bad-doc",
            event_id=seed_event.event_id,
            patient_id=seed_patient.patient_id,
            logged_by=seed_staff[0].staff_id,
            doc_type="invalid_doc",  # not allowed
        )
        db.add(bad_enc)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_encounter_triage_level_constraint(self, db, seed_event, seed_patient, seed_staff):
        bad_enc = Encounter(
            encounter_id="enc-bad-triage",
            event_id=seed_event.event_id,
            patient_id=seed_patient.patient_id,
            logged_by=seed_staff[0].staff_id,
            doc_type="pcr",
            triage_level="purple",  # not allowed
        )
        db.add(bad_enc)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_encounter_disposition_constraint(self, db, seed_event, seed_patient, seed_staff):
        bad_enc = Encounter(
            encounter_id="enc-bad-disp",
            event_id=seed_event.event_id,
            patient_id=seed_patient.patient_id,
            logged_by=seed_staff[0].staff_id,
            doc_type="pcr",
            disposition="flight_home",  # not allowed
        )
        db.add(bad_enc)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


# ── IncidentQueue ────────────────────────────────────────────────────────────

class TestIncidentQueueModel:
    def test_create_incident(self, db, seed_event, seed_patient, seed_staff, seed_encounter):
        incident = IncidentQueue(
            incident_id="inc-1",
            event_id=seed_event.event_id,
            patient_id=seed_patient.patient_id,
            encounter_id=seed_encounter.encounter_id,
            status="dispatched",
            assigned_to=seed_staff[0].staff_id,
            location="stage_left",
            priority="red",
            radio_notes="Medic dispatching to main stage left for collapse.",
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)
        
        saved = db.query(IncidentQueue).filter(IncidentQueue.incident_id == "inc-1").first()
        assert saved.status == "dispatched"
        assert saved.location == "stage_left"
        assert saved.priority == "red"

    def test_incident_status_constraint(self, db, seed_event, seed_patient, seed_staff):
        bad_inc = IncidentQueue(
            incident_id="inc-bad-status",
            event_id=seed_event.event_id,
            patient_id=seed_patient.patient_id,
            assigned_to=seed_staff[0].staff_id,
            status="flying",  # not allowed
        )
        db.add(bad_inc)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


# ── ReagentLog ───────────────────────────────────────────────────────────────

class TestReagentLogModel:
    def test_create_reagent_log(self, db, seed_reagent_log):
        log = db.query(ReagentLog).filter(ReagentLog.log_id == "log-1").first()
        assert log.test_type == "marquis"
        assert log.test_result == "color_change_verified"
        assert log.disclaimer_agreed is True

    def test_reagent_test_type_constraint(self, db, seed_event, seed_staff):
        bad_log = ReagentLog(
            log_id="log-bad-type",
            event_id=seed_event.event_id,
            tester_staff_id=seed_staff[0].staff_id,
            sample_description="Pill",
            test_type="ph_paper",  # not allowed
            test_result="positive",
        )
        db.add(bad_log)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


# ── Supply ───────────────────────────────────────────────────────────────────

class TestSupplyModel:
    def test_create_supply(self, db, seed_supply):
        sup = db.query(Supply).filter(Supply.supply_id == "sup-1").first()
        assert sup.name == "Naloxone Nasal Spray"
        assert sup.category == "narcan"
        assert sup.quantity_remaining == 45

    def test_supply_category_constraint(self, db, seed_event):
        bad_sup = Supply(
            supply_id="sup-bad-cat",
            event_id=seed_event.event_id,
            name="Mystery Pill",
            category="candy",  # not allowed
            quantity_start=10,
            quantity_remaining=10,
        )
        db.add(bad_sup)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
