"""
Integration tests for API endpoints (backend/routers/).
Uses FastAPI TestClient with an isolated SQLite database.
"""
import json
import pytest
from datetime import datetime, date

class TestHealthcheck:
    def test_healthcheck(self, client):
        r = client.get("/healthz")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
        assert r.json()["service"] == "event-med-ai"


class TestEventRouter:
    def test_list_events(self, client, seed_event):
        r = client.get("/api/event")
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["name"] == "Griztronics 2026"

    def test_create_event(self, client):
        payload = {
            "name": "Bass Canyon 2026",
            "venue": "The Gorge",
            "weather_high_f": 92.0,
            "weather_humidity": 15.0,
        }
        r = client.post("/api/event", json=payload)
        assert r.status_code == 201
        assert r.json()["name"] == "Bass Canyon 2026"


class TestPatientRouter:
    def test_list_patients_empty(self, client):
        r = client.get("/api/patient")
        assert r.status_code == 200
        assert r.json() == []

    def test_create_patient(self, client, seed_event):
        payload = {
            "event_id": seed_event.event_id,
            "identifier": "Green Band #101",
            "approx_age": 19,
            "gender": "M",
            "location_found": "campground",
            "known_allergies": ["Peanuts"],
        }
        r = client.post("/api/patient", json=payload)
        assert r.status_code == 201
        assert r.json()["identifier"] == "Green Band #101"
        assert r.json()["known_allergies"] == ["Peanuts"]

    def test_get_patient(self, client, seed_patient):
        r = client.get(f"/api/patient/{seed_patient.patient_id}")
        assert r.status_code == 200
        assert r.json()["identifier"] == "Red Band #42"

    def test_get_patient_not_found(self, client):
        r = client.get("/api/patient/nonexistent")
        assert r.status_code == 404

    def test_update_patient(self, client, seed_patient):
        r = client.patch(
            f"/api/patient/{seed_patient.patient_id}",
            json={"approx_age": 25, "location_found": "gate"},
        )
        assert r.status_code == 200
        assert r.json()["approx_age"] == 25
        assert r.json()["location_found"] == "gate"

    def test_delete_patient(self, client, seed_patient):
        r = client.delete(f"/api/patient/{seed_patient.patient_id}")
        assert r.status_code == 204
        r = client.get(f"/api/patient/{seed_patient.patient_id}")
        assert r.status_code == 404


class TestEncounterRouter:
    def test_create_encounter(self, client, seed_event, seed_patient, seed_staff):
        payload = {
            "event_id": seed_event.event_id,
            "patient_id": seed_patient.patient_id,
            "doc_type": "pcr",
            "logged_by": seed_staff[0].staff_id,
            "chief_complaint": "Dehydration",
            "triage_level": "green",
            "disposition": "released",
        }
        r = client.post("/api/encounter", json=payload)
        assert r.status_code == 201
        assert r.json()["chief_complaint"] == "Dehydration"

    def test_get_encounter_not_found(self, client):
        r = client.get("/api/encounter/nonexistent")
        assert r.status_code == 404


class TestStaffRouter:
    def test_create_staff(self, client, seed_event):
        payload = {
            "event_id": seed_event.event_id,
            "name": "Dr. Smith",
            "role": "md",
            "call_sign": "Doc-2",
        }
        r = client.post("/api/staff", json=payload)
        assert r.status_code == 201
        assert r.json()["call_sign"] == "Doc-2"


class TestReagentRouter:
    def test_create_reagent_log(self, client, seed_event, seed_staff, seed_patient):
        payload = {
            "event_id": seed_event.event_id,
            "patient_id": seed_patient.patient_id,
            "sample_description": "Blue pill",
            "test_type": "fent_strip",
            "test_result": "negative",
            "disclaimer_agreed": True,
            "tester_staff_id": seed_staff[0].staff_id,
        }
        r = client.post("/api/reagent", json=payload)
        assert r.status_code == 201
        assert r.json()["sample_description"] == "Blue pill"

    def test_create_reagent_log_denied_if_disclaimer_false(self, client, seed_event, seed_staff, seed_patient):
        payload = {
            "event_id": seed_event.event_id,
            "patient_id": seed_patient.patient_id,
            "sample_description": "Blue pill",
            "test_type": "fent_strip",
            "test_result": "negative",
            "disclaimer_agreed": False,
            "tester_staff_id": seed_staff[0].staff_id,
        }
        r = client.post("/api/reagent", json=payload)
        assert r.status_code == 400
        assert "disclaimer" in r.json()["detail"].lower()


class TestSuppliesRouter:
    def test_list_supplies(self, client, seed_supply):
        r = client.get("/api/supplies")
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["name"] == "Naloxone Nasal Spray"


class TestHospitalsRouter:
    def test_list_hospitals(self, client, seed_hospital):
        r = client.get("/api/hospitals")
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["name"] == "Samaritan Hospital"


class TestSetupRouter:
    def test_get_setup_status(self, client):
        r = client.get("/api/setup/status")
        assert r.status_code == 200
        assert "ollama_installed" in r.json()

    def test_get_event_info(self, client):
        r = client.get("/api/setup/event-info")
        assert r.status_code == 200
        assert r.json()["name"] == "Griztronics 2026"

    def test_reset_demo_data(self, client):
        r = client.post("/api/setup/reset-demo-data")
        assert r.status_code == 200
        assert r.json()["status"] == "success"
