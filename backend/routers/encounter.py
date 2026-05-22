import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from backend.db.database import get_db
from backend.db.models import Encounter, Patient
from backend.schemas.pydantic_models import EncounterRead, EncounterCreate, EncounterUpdate

router = APIRouter()


@router.get("", response_model=List[EncounterRead])
def list_encounters(
    event_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    doc_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Encounter)
    if event_id:
        query = query.filter(Encounter.event_id == event_id)
    if patient_id:
        query = query.filter(Encounter.patient_id == patient_id)
    if doc_type:
        query = query.filter(Encounter.doc_type == doc_type)
    return query.order_by(Encounter.encounter_time.desc()).all()


@router.get("/{encounter_id}", response_model=EncounterRead)
def get_encounter(encounter_id: str, db: Session = Depends(get_db)):
    encounter = db.query(Encounter).filter(Encounter.encounter_id == encounter_id).first()
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")
    return encounter


@router.post("", response_model=EncounterRead, status_code=201)
def create_encounter(payload: EncounterCreate, db: Session = Depends(get_db)):
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.patient_id == payload.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    vital_signs_str = json.dumps(payload.vital_signs.model_dump() if payload.vital_signs else {})
    interventions_str = json.dumps([intv.model_dump() for intv in (payload.interventions or [])])
    
    encounter = Encounter(
        event_id=payload.event_id,
        patient_id=payload.patient_id,
        doc_type=payload.doc_type,
        logged_by=payload.logged_by,
        encounter_time=payload.encounter_time or datetime.utcnow(),
        chief_complaint=payload.chief_complaint,
        symptoms=json.dumps(payload.symptoms or []),
        vital_signs=vital_signs_str,
        substances_involved=json.dumps(payload.substances_involved or []),
        triage_level=payload.triage_level,
        escalated_to=payload.escalated_to,
        escalation_time=payload.escalation_time,
        interventions=interventions_str,
        disposition=payload.disposition,
        transport_hospital=payload.transport_hospital,
        transport_unit=payload.transport_unit,
        transport_time=payload.transport_time,
        ama_documented=payload.ama_documented or False,
        ama_capacity_assessment=payload.ama_capacity_assessment,
        photo_paths=json.dumps(payload.photo_paths or []),
        notes=payload.notes,
    )
    
    # If disposition is transport or deceased, or if the encounter is closed, we can toggle patient is_active = False
    if payload.disposition in ("transport", "deceased", "released") and payload.doc_type == "pcr":
        # Note: released might mean they left, but we can let the operator decide whether to deactivate.
        # For simplicity, if disposition is transport or deceased, we mark the patient inactive.
        if payload.disposition in ("transport", "deceased"):
            patient.is_active = False

    db.add(encounter)
    db.commit()
    db.refresh(encounter)
    return encounter


@router.patch("/{encounter_id}", response_model=EncounterRead)
def update_encounter(encounter_id: str, payload: EncounterUpdate, db: Session = Depends(get_db)):
    encounter = db.query(Encounter).filter(Encounter.encounter_id == encounter_id).first()
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")
        
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field in ("symptoms", "substances_involved", "photo_paths") and value is not None:
            value = json.dumps(value)
        elif field == "vital_signs" and value is not None:
            value = json.dumps(value.model_dump())
        elif field == "interventions" and value is not None:
            value = json.dumps([intv.model_dump() for intv in value])
            
        setattr(encounter, field, value)
        
    # Also handle patient activation if disposition changed
    if payload.disposition in ("transport", "deceased"):
        patient = db.query(Patient).filter(Patient.patient_id == encounter.patient_id).first()
        if patient:
            patient.is_active = False
            
    db.commit()
    db.refresh(encounter)
    return encounter


@router.delete("/{encounter_id}", status_code=204)
def delete_encounter(encounter_id: str, db: Session = Depends(get_db)):
    encounter = db.query(Encounter).filter(Encounter.encounter_id == encounter_id).first()
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")
    db.delete(encounter)
    db.commit()
    return None
