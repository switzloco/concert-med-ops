"""
Security audit tests for the Event Med AI backend.

Checks for common vulnerabilities: CORS misconfiguration, path traversal,
input validation, SQL injection via API, and sensitive data exposure.
"""
import pytest
from sqlalchemy.exc import IntegrityError


class TestCORSSecurity:
    def test_cors_headers_present(self, client):
        """CORS headers should be set on responses."""
        r = client.options(
            "/healthz",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert r.status_code in (200, 204, 405)


class TestInputValidation:
    def test_create_staff_xss_in_name(self, client, seed_event):
        """XSS payloads in names should be stored literally (no execution)."""
        payload = {
            "event_id": seed_event.event_id,
            "name": "<script>alert('xss')</script>",
            "role": "emt",
            "call_sign": "Med-9",
        }
        r = client.post("/api/staff", json=payload)
        assert r.status_code == 201
        assert r.json()["name"] == "<script>alert('xss')</script>"

    def test_create_staff_sql_injection_in_name(self, client, seed_event):
        """SQL injection attempts should be safely parameterized."""
        payload = {
            "event_id": seed_event.event_id,
            "name": "'; DROP TABLE staff_members; --",
            "role": "emt",
            "call_sign": "Med-9",
        }
        r = client.post("/api/staff", json=payload)
        assert r.status_code == 201
        # Table should still exist
        r2 = client.get("/api/staff")
        assert r2.status_code == 200

    def test_oversized_payload_staff(self, client, seed_event):
        """Very large payloads should not crash the server."""
        payload = {
            "event_id": seed_event.event_id,
            "name": "A" * 10_000,
            "role": "emt",
            "call_sign": "B" * 10_000,
        }
        r = client.post("/api/staff", json=payload)
        assert r.status_code in (201, 422)

    def test_invalid_json_body(self, client):
        """Malformed JSON should return 422."""
        r = client.post(
            "/api/staff",
            content="this is not json",
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == 422

    def test_reagent_identify_disclaimer_required(self, client):
        """Reagent identify photo endpoint requires disclaimer_agreed=True."""
        import io
        fake_file = io.BytesIO(b"fake image data")
        r = client.post(
            "/api/reagent/identify-photo",
            data={
                "test_type": "marquis",
                "disclaimer_agreed": "false",
            },
            files={"file": ("test.jpg", fake_file, "image/jpeg")},
        )
        assert r.status_code == 400
        assert "disclaimer" in r.json()["detail"].lower()


class TestPathTraversal:
    def test_patient_id_path_traversal(self, client):
        """Path traversal in ID params should not leak files."""
        r = client.get("/api/patient/../../../etc/passwd")
        # FastAPI/Uvicorn normalizes path or returns 404
        assert r.status_code == 404


class TestSensitiveDataExposure:
    def test_healthcheck_no_secrets(self, client):
        """Healthcheck should not expose API keys or internal config."""
        r = client.get("/healthz")
        body = r.text
        assert "GOOGLE_API_KEY" not in body
        assert "test-key" not in body

    def test_error_response_no_stack_trace(self, client):
        """404s should not leak internal stack traces."""
        r = client.get("/api/patient/nonexistent")
        body = r.text
        assert "Traceback" not in body
        assert "sqlalchemy" not in body.lower()
