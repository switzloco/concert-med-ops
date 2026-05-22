import os
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.db.database import Base, engine
from backend.routers import (
    event, patient, encounter, reagent, tracking,
    hospitals, staff, supplies, ai, setup, uploads
)
from backend.logger import logger

app = FastAPI(
    title="Event Med AI",
    description="Clinical Decision Support and Whiteboard for Festival Medicine",
    version="0.1.0",
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    for error in exc.errors():
        loc = error.get("loc", [])
        msg = error.get("msg", "")
        if "disclaimer_agreed" in loc or "disclaimer" in msg.lower():
            return JSONResponse(
                status_code=400,
                content={"detail": msg or "You must read and agree to the liability disclaimer before logging drug testing results."}
            )
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

# Serve uploads as static files
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# Create tables on startup
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.debug(f"Incoming request: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.debug(f"Completed {request.method} {request.url.path} with status {response.status_code} in {process_time:.4f}s")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.exception(f"Request failed: {request.method} {request.url.path} after {process_time:.4f}s - {str(e)}")
        raise

@app.get("/healthz", tags=["system"])
@app.get("/healthz/", tags=["system"])
def healthcheck():
    return {"status": "ok", "service": "event-med-ai", "version": "0.1.0"}

# Include Routers
app.include_router(event.router, prefix="/api/event", tags=["event"])
app.include_router(patient.router, prefix="/api/patient", tags=["patient"])
app.include_router(encounter.router, prefix="/api/encounter", tags=["encounter"])
app.include_router(reagent.router, prefix="/api/reagent", tags=["reagent"])
app.include_router(tracking.router, prefix="/api/tracking", tags=["tracking"])
app.include_router(hospitals.router, prefix="/api/hospitals", tags=["hospitals"])
app.include_router(staff.router, prefix="/api/staff", tags=["staff"])
app.include_router(supplies.router, prefix="/api/supplies", tags=["supplies"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(setup.router, prefix="/api/setup", tags=["setup"])
app.include_router(uploads.router, prefix="/api/uploads", tags=["uploads"])

# Serve the embedded Next.js static export when present
_FRONTEND = Path(__file__).parent.parent / "frontend_out"
if _FRONTEND.is_dir():
    app.mount("/_next", StaticFiles(directory=str(_FRONTEND / "_next")), name="nextjs-assets")
    
    if (_FRONTEND / "images").is_dir():
        app.mount("/images", StaticFiles(directory=str(_FRONTEND / "images")), name="public-images")
    if (_FRONTEND / "favicon.ico").is_file():
        @app.get("/favicon.ico", include_in_schema=False)
        async def favicon():
            return FileResponse(str(_FRONTEND / "favicon.ico"))

    @app.get("/", include_in_schema=False)
    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str = ""):
        file_path = _FRONTEND / full_path
        if full_path and file_path.is_file():
            return FileResponse(str(file_path))

        index_candidate = _FRONTEND / full_path / "index.html"
        if index_candidate.is_file():
            return FileResponse(str(index_candidate))

        return FileResponse(str(_FRONTEND / "index.html"))
