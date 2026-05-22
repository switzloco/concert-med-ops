"""
Shared pytest fixtures for the Event Med AI backend test suite.

Uses an in-memory SQLite database so tests are fast, isolated,
and don't touch the production event_med.db file.
"""
import json
import os
import pytest
from datetime import datetime, date
from unittest.mock import AsyncMock, MagicMock, patch

# ── Environment overrides (must happen BEFORE any backend imports) ───────────
os.environ["DATABASE_URL"] = "sqlite:///./test_event_med.db"
os.environ["CLOUD_MODE"] = "false"
os.environ["GOOGLE_API_KEY"] = "test-key-not-real"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

from backend.db.database import Base, get_db
from backend.db.models import (
    Event, StaffMember, Patient, Encounter, IncidentQueue,
    HospitalDirectory, ReagentLog, Supply
)
from backend.main import app

# ── In-memory SQLite engine ──────────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite:///./test_event_med.db"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)


@event.listens_for(test_engine, "connect")
def _set_pragmas(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def _override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


# ── Database lifecycle ───────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def setup_database():
    """Create all tables before each test, drop after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db():
    """Provide a clean database session for direct model testing."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client():
    """TestClient wired to the overridden DB."""
    return TestClient(app)


# ── Seed data fixtures ──────────────────────────────────────────────────────

@pytest.fixture()
def seed_event(db):
    """Insert a single test event and return it."""
    evt = Event(
        event_id="test-event-1",
        name="Griztronics 2026",
        venue="The Gorge Amphitheatre",
        date_start=datetime(2026, 7, 10, 12, 0),
        date_end=datetime(2026, 7, 13, 12, 0),
        expected_attendance=22500,
        medical_lead="Dr. Sarah Jenkins, MD",
        contact_info="Radio: Doc-1",
        weather_high_f=85.0,
        weather_humidity=22.0,
        notes="Test event notes.",
    )
    db.add(evt)
    db.commit()
    db.refresh(evt)
    return evt


@pytest.fixture()
def seed_staff(db, seed_event):
    """Insert staff members and return them."""
    staff = [
        StaffMember(
            staff_id="staff-1",
            event_id=seed_event.event_id,
            name="Alice RN",
            role="rn",
            call_sign="Med-1",
            is_on_shift=True,
        ),
        StaffMember(
            staff_id="staff-2",
            event_id=seed_event.event_id,
            name="Bob MD",
            role="md",
            call_sign="Doc-1",
            is_on_shift=True,
        ),
        StaffMember(
            staff_id="staff-3",
            event_id=seed_event.event_id,
            name="Charlie EMT",
            role="emt",
            call_sign="Med-2",
            is_on_shift=False,
        ),
    ]
    db.add_all(staff)
    db.commit()
    for s in staff:
        db.refresh(s)
    return staff


@pytest.fixture()
def seed_patient(db, seed_event):
    """Insert a test patient."""
    patient = Patient(
        patient_id="patient-1",
        event_id=seed_event.event_id,
        identifier="Red Band #42",
        approx_age=24,
        gender="F",
        weight_kg=60.0,
        known_allergies=json.dumps(["Penicillin"]),
        known_medications=json.dumps(["Lexapro"]),
        known_conditions=json.dumps(["Asthma"]),
        substances_reported=json.dumps([{"name": "MDMA", "route": "oral", "time_taken": "3 hours ago", "amount": "1 pill"}]),
        location_found="venue_tent",
        is_active=True,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@pytest.fixture()
def seed_encounter(db, seed_event, seed_patient, seed_staff):
    """Insert a test encounter."""
    enc = Encounter(
        encounter_id="enc-1",
        event_id=seed_event.event_id,
        patient_id=seed_patient.patient_id,
        doc_type="pcr",
        logged_by=seed_staff[0].staff_id,
        encounter_time=datetime.utcnow(),
        chief_complaint="Palpitations and anxiety",
        symptoms=json.dumps(["anxiety", "tachycardia"]),
        vital_signs=json.dumps({"hr": 115, "bp": "140/90", "temp_f": 99.8, "spo2": 98, "rr": 20, "gcs": 15}),
        substances_involved=json.dumps(["MDMA"]),
        triage_level="yellow",
        disposition="observation",
        notes="Patient monitored in medical tent.",
    )
    db.add(enc)
    db.commit()
    db.refresh(enc)
    return enc


@pytest.fixture()
def seed_hospital(db):
    """Insert a test hospital."""
    hosp = HospitalDirectory(
        hospital_id="hosp-1",
        name="Samaritan Hospital",
        distance_miles=43.0,
        drive_time_min=43,
        trauma_level=3,
        capabilities=json.dumps(["cardiac", "psych"]),
        phone="509-555-0100",
        address="801 E Wheeler Rd, Moses Lake, WA",
        is_on_diversion=False,
        notes="General regional hospital",
    )
    db.add(hosp)
    db.commit()
    db.refresh(hosp)
    return hosp


@pytest.fixture()
def seed_supply(db, seed_event):
    """Insert a test supply item."""
    sup = Supply(
        supply_id="sup-1",
        event_id=seed_event.event_id,
        name="Naloxone Nasal Spray",
        category="narcan",
        quantity_start=50,
        quantity_used=5,
        quantity_remaining=45,
        expiration_date=date(2027, 12, 31),
        lot_number="LOT12345",
        location="venue_tent",
        notes="Stored in critical locker",
    )
    db.add(sup)
    db.commit()
    db.refresh(sup)
    return sup


@pytest.fixture()
def seed_reagent_log(db, seed_event, seed_staff, seed_patient):
    """Insert a test reagent check log."""
    log = ReagentLog(
        log_id="log-1",
        event_id=seed_event.event_id,
        patient_id=seed_patient.patient_id,
        sample_description="Yellow powder",
        test_type="marquis",
        test_result="color_change_verified",
        color_observed="Black/Purple",
        predicted_substance="MDMA",
        disclaimer_agreed=True,
        tester_staff_id=seed_staff[1].staff_id,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
