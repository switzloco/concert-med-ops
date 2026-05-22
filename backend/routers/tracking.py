from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from backend.db.database import get_db
from backend.db.models import IncidentQueue, Patient
from backend.schemas.pydantic_models import IncidentQueueRead, IncidentQueueCreate, IncidentQueueUpdate

router = APIRouter()


@router.get("", response_model=List[IncidentQueueRead])
def list_incidents(
    event_id: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    query = db.query(IncidentQueue)
    if event_id:
        query = query.filter(IncidentQueue.event_id == event_id)
    if active_only:
        # Show all except cleared
        query = query.filter(IncidentQueue.status != "cleared")
    return query.order_by(IncidentQueue.priority.desc(), IncidentQueue.dispatch_time.asc()).all()


@router.get("/{incident_id}", response_model=IncidentQueueRead)
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    incident = db.query(IncidentQueue).filter(IncidentQueue.incident_id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("", response_model=IncidentQueueRead, status_code=201)
def create_incident(payload: IncidentQueueCreate, db: Session = Depends(get_db)):
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.patient_id == payload.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    incident = IncidentQueue(
        event_id=payload.event_id,
        patient_id=payload.patient_id,
        encounter_id=payload.encounter_id,
        status="dispatched",
        assigned_to=payload.assigned_to,
        location=payload.location,
        priority=payload.priority,
        dispatch_time=datetime.utcnow(),
        radio_notes=payload.radio_notes,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


@router.patch("/{incident_id}", response_model=IncidentQueueRead)
def update_incident(incident_id: str, payload: IncidentQueueUpdate, db: Session = Depends(get_db)):
    incident = db.query(IncidentQueue).filter(IncidentQueue.incident_id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(incident, field, value)

    # Set times dynamically based on status transitions
    if payload.status == "on_scene" and not incident.arrival_time:
        incident.arrival_time = datetime.utcnow()
    elif payload.status == "cleared" and not incident.cleared_time:
        incident.cleared_time = datetime.utcnow()

    db.commit()
    db.refresh(incident)
    return incident


@router.delete("/{incident_id}", status_code=204)
def delete_incident(incident_id: str, db: Session = Depends(get_db)):
    incident = db.query(IncidentQueue).filter(IncidentQueue.incident_id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    db.delete(incident)
    db.commit()
    return None
