import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.db.database import get_db
from backend.db.models import HospitalDirectory
from backend.schemas.pydantic_models import HospitalDirectoryRead, HospitalDirectoryCreate, HospitalDirectoryUpdate

router = APIRouter()


@router.get("", response_model=List[HospitalDirectoryRead])
def list_hospitals(db: Session = Depends(get_db)):
    return db.query(HospitalDirectory).all()


@router.get("/{hospital_id}", response_model=HospitalDirectoryRead)
def get_hospital(hospital_id: str, db: Session = Depends(get_db)):
    hospital = db.query(HospitalDirectory).filter(HospitalDirectory.hospital_id == hospital_id).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return hospital


@router.post("", response_model=HospitalDirectoryRead, status_code=201)
def create_hospital(payload: HospitalDirectoryCreate, db: Session = Depends(get_db)):
    hospital = HospitalDirectory(
        name=payload.name,
        distance_miles=payload.distance_miles,
        drive_time_min=payload.drive_time_min,
        trauma_level=payload.trauma_level,
        capabilities=json.dumps(payload.capabilities or []),
        phone=payload.phone,
        address=payload.address,
        is_on_diversion=payload.is_on_diversion,
        notes=payload.notes,
    )
    db.add(hospital)
    db.commit()
    db.refresh(hospital)
    return hospital


@router.patch("/{hospital_id}", response_model=HospitalDirectoryRead)
def update_hospital(hospital_id: str, payload: HospitalDirectoryUpdate, db: Session = Depends(get_db)):
    hospital = db.query(HospitalDirectory).filter(HospitalDirectory.hospital_id == hospital_id).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "capabilities" and value is not None:
            value = json.dumps(value)
        setattr(hospital, field, value)

    db.commit()
    db.refresh(hospital)
    return hospital


@router.delete("/{hospital_id}", status_code=204)
def delete_hospital(hospital_id: str, db: Session = Depends(get_db)):
    hospital = db.query(HospitalDirectory).filter(HospitalDirectory.hospital_id == hospital_id).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    db.delete(hospital)
    db.commit()
    return None
