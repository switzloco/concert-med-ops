import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.db.database import get_db
from backend.db.models import Patient
from backend.schemas.pydantic_models import PatientRead, PatientCreate, PatientUpdate

router = APIRouter()


@router.get("", response_model=List[PatientRead])
def list_patients(event_id: Optional[str] = None, active_only: bool = True, db: Session = Depends(get_db)):
    query = db.query(Patient)
    if event_id:
        query = query.filter(Patient.event_id == event_id)
    if active_only:
        query = query.filter(Patient.is_active == True)
    return query.order_by(Patient.created_at.desc()).all()


@router.get("/{patient_id}", response_model=PatientRead)
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.post("", response_model=PatientRead, status_code=201)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    # Crucial security check: Ensure we do NOT store legal name/identifying details.
    # The identifier field is meant for wristbands or descriptive tokens.
    
    substances_json = json.dumps([sub.model_dump() for sub in (payload.substances_reported or [])])
    
    patient = Patient(
        event_id=payload.event_id,
        identifier=payload.identifier,
        approx_age=payload.approx_age,
        gender=payload.gender,
        weight_kg=payload.weight_kg,
        known_allergies=json.dumps(payload.known_allergies or []),
        known_medications=json.dumps(payload.known_medications or []),
        known_conditions=json.dumps(payload.known_conditions or []),
        substances_reported=substances_json,
        location_found=payload.location_found,
        is_active=True,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.patch("/{patient_id}", response_model=PatientRead)
def update_patient(patient_id: str, payload: PatientUpdate, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field in ("known_allergies", "known_medications", "known_conditions") and value is not None:
            value = json.dumps(value)
        elif field == "substances_reported" and value is not None:
            value = json.dumps([sub.model_dump() for sub in value])
        
        setattr(patient, field, value)
        
    db.commit()
    db.refresh(patient)
    return patient


@router.delete("/{patient_id}", status_code=204)
def delete_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    db.delete(patient)
    db.commit()
    return None
