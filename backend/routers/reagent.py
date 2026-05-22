import json
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from backend.db.database import get_db
from backend.db.models import ReagentLog
from backend.schemas.pydantic_models import ReagentLogRead, ReagentLogCreate
from backend.config import settings
from google import genai
from google.genai import types

router = APIRouter()

# Enforce UPLOAD_DIR
UPLOAD_DIR = Path(settings.upload_dir)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("", response_model=List[ReagentLogRead])
def list_reagent_logs(event_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(ReagentLog)
    if event_id:
        query = query.filter(ReagentLog.event_id == event_id)
    return query.order_by(ReagentLog.created_at.desc()).all()


@router.post("", response_model=ReagentLogRead, status_code=201)
def create_reagent_log(payload: ReagentLogCreate, db: Session = Depends(get_db)):
    # Explicit check in router as well, even though Pydantic validates it
    if not payload.disclaimer_agreed:
        raise HTTPException(
            status_code=400,
            detail="You must read and agree to the liability disclaimer before logging drug testing results."
        )

    log = ReagentLog(
        event_id=payload.event_id,
        patient_id=payload.patient_id,
        sample_description=payload.sample_description,
        test_type=payload.test_type,
        test_result=payload.test_result,
        color_observed=payload.color_observed,
        predicted_substance=payload.predicted_substance,
        disclaimer_agreed=payload.disclaimer_agreed,
        tester_staff_id=payload.tester_staff_id,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.post("/identify-photo")
async def identify_photo(
    file: UploadFile = File(...),
    test_type: str = Form(...),  # e.g., "marquis", "mecke", "fent_strip", "pill_visual"
    disclaimer_agreed: bool = Form(...)
):
    """Identify substance or reagent reaction from image using Gemini API."""
    if not disclaimer_agreed:
        raise HTTPException(
            status_code=400,
            detail="You must agree to the liability disclaimer before running pill identification."
        )

    # Read image bytes
    img_bytes = await file.read()

    # Define standard disclaimer
    mandatory_disclaimer = (
        "Reagent color change is only presumptive. Reagent testing cannot determine purity "
        "or exact concentration, and is easily masked by mixtures. Fentanyl test strips "
        "have a limit of detection and may produce false negatives if not prepared correctly. "
        "This is NOT a lab-grade confirmatory check. Event Med AI does not guarantee "
        "safety or encourage drug consumption."
    )

    # If google_api_key is available, query Gemini API. Else, run presumptive fallback rules.
    api_key = settings.google_api_key
    if api_key and settings.cloud_mode:
        try:
            client = genai.Client(api_key=api_key)
            prompt = (
                f"You are a clinical decisions tool helping a festival medical supervisor. "
                f"Analyze this image of a substance testing result. The user specified test type: '{test_type}'. "
                f"First, describe what you see (e.g. colors, textures, pill shape/markings). "
                f"Second, give a presumptive/preliminary assessment (e.g., if marquis and turns purple/black, MDMA/MDA is likely. "
                f"If fentanyl strip, look for one vs two lines). "
                f"Third, state the limitations and print the following disclaimer exactly: '{mandatory_disclaimer}'. "
                f"Keep your analysis clinical, professional, and highlight warning signs."
            )
            config = types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=1024,
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                    prompt
                ],
                config=config,
            )
            
            return {
                "analysis": response.text,
                "disclaimer": mandatory_disclaimer,
                "status": "success"
            }
        except Exception as e:
            # Fall back to structured local response if API call fails
            pass

    # Presumptive local fallback based on test_type
    fallback_text = ""
    if test_type == "fent_strip":
        fallback_text = (
            "Presumptive local analysis: Fentanyl test strip. "
            "Please check lines: ONE line = POSITIVE for fentanyl. TWO lines = NEGATIVE. "
            "If no lines appear, the test is invalid.\n\n"
        )
    elif test_type == "marquis":
        fallback_text = (
            "Presumptive local analysis: Marquis reagent. "
            "Expected reaction colors:\n"
            "- MDMA/MDA/MDE: Purple to Black (fast)\n"
            "- Amphetamine/Methamphetamine: Orange to Brown\n"
            "- 2C-B: Yellow to Green\n"
            "- Heroin/Morphine: Purple/Pink\n"
            "- DXM: Yellow to Orange\n\n"
        )
    elif test_type == "mecke":
        fallback_text = (
            "Presumptive local analysis: Mecke reagent. "
            "Expected reaction colors:\n"
            "- MDMA/MDA/MDE: Green to Blue/Black\n"
            "- Heroin/Morphine: Green to Blue\n"
            "- DXM: Yellow\n\n"
        )
    else:
        fallback_text = (
            "Presumptive local analysis: Pill/Substance visual. "
            "Cannot determine contents or presence of active ingredients by visual shape/color alone.\n\n"
        )

    fallback_text += f"\nDISCLAIMER:\n{mandatory_disclaimer}"

    return {
        "analysis": fallback_text,
        "disclaimer": mandatory_disclaimer,
        "status": "fallback"
    }
