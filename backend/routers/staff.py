from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.db.database import get_db
from backend.db.models import StaffMember
from backend.schemas.pydantic_models import StaffMemberRead, StaffMemberCreate, StaffMemberUpdate

router = APIRouter()


@router.get("", response_model=List[StaffMemberRead])
def list_staff(event_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(StaffMember)
    if event_id:
        query = query.filter(StaffMember.event_id == event_id)
    return query.all()


@router.get("/{staff_id}", response_model=StaffMemberRead)
def get_staff_member(staff_id: str, db: Session = Depends(get_db)):
    member = db.query(StaffMember).filter(StaffMember.staff_id == staff_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Staff member not found")
    return member


@router.post("", response_model=StaffMemberRead, status_code=201)
def create_staff_member(payload: StaffMemberCreate, db: Session = Depends(get_db)):
    member = StaffMember(
        event_id=payload.event_id,
        name=payload.name,
        role=payload.role,
        call_sign=payload.call_sign,
        is_on_shift=payload.is_on_shift,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.patch("/{staff_id}", response_model=StaffMemberRead)
def update_staff_member(staff_id: str, payload: StaffMemberUpdate, db: Session = Depends(get_db)):
    member = db.query(StaffMember).filter(StaffMember.staff_id == staff_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Staff member not found")
    
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(member, field, value)
        
    db.commit()
    db.refresh(member)
    return member


@router.delete("/{staff_id}", status_code=204)
def delete_staff_member(staff_id: str, db: Session = Depends(get_db)):
    member = db.query(StaffMember).filter(StaffMember.staff_id == staff_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Staff member not found")
    db.delete(member)
    db.commit()
    return None
