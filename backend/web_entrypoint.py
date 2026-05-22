"""Web deployment entrypoint (Cloud Run / Railway / any PaaS).

Distinct from entrypoint.py (PyInstaller desktop) — this one:
 - Listens on 0.0.0.0:$PORT (Cloud Run injects PORT)
 - Runs Alembic migrations before starting
 - Auto-seeds demo data if the DB is empty (so judges see Griztronics 2026 on first visit)
 - Never touches sys._MEIPASS or frozen-binary paths
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _ensure_data_dir() -> Path:
    data_dir = Path(os.environ.get("EVENT_MED_DATA_DIR", "/data"))
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "uploads").mkdir(exist_ok=True)
    return data_dir


def _run_migrations() -> None:
    # If migrations aren't needed or Alembic is not set up yet,
    # we can run a simple check or run it if alembic.ini is present.
    if not os.path.exists("alembic.ini"):
        print("alembic.ini not found. Skipping migration step.")
        return
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise RuntimeError("Alembic upgrade failed")
    print(result.stdout or "✓ Migrations up to date.")


def _auto_seed() -> None:
    from backend.db.database import SessionLocal
    from backend.db.models import Event

    db = SessionLocal()
    try:
        if db.query(Event).first():
            print("✓ DB already seeded — skipping.")
            return
    finally:
        db.close()

    print("Seeding demo data (Griztronics 2026)…")
    from backend.data.seed_demo import seed_database
    db = SessionLocal()
    try:
        seed_database(db)
        print("✓ Demo data seeded successfully.")
    except Exception as e:
        print(f"Error seeding demo data: {e}", file=sys.stderr)
        db.rollback()
    finally:
        db.close()


def main() -> None:
    data_dir = _ensure_data_dir()
    os.environ.setdefault("DATABASE_URL", f"sqlite:///{data_dir}/event_med.db")

    # Only run migrations if we are using Alembic
    _run_migrations()
    _auto_seed()

    import uvicorn
    from backend.main import app

    port = int(os.environ.get("PORT", "8080"))
    print(f"Starting Event Med AI on 0.0.0.0:{port}...")
    print(f"DATABASE_URL: {os.environ.get('DATABASE_URL')}")
    
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        from backend.config import settings
        api_key = settings.google_api_key
        
    print(f"GOOGLE_API_KEY: {'[SET, len=' + str(len(api_key)) + ']' if api_key else '[MISSING]'}")
    print(f"CLOUD_MODE: {os.environ.get('CLOUD_MODE', 'false')}")
    
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
