from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.db.database import get_db
from backend.db.models import Supply
from backend.schemas.pydantic_models import SupplyRead, SupplyCreate, SupplyUpdate

router = APIRouter()


@router.get("", response_model=List[SupplyRead])
def list_supplies(event_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Supply)
    if event_id:
        query = query.filter(Supply.event_id == event_id)
    return query.all()


@router.get("/{supply_id}", response_model=SupplyRead)
def get_supply(supply_id: str, db: Session = Depends(get_db)):
    supply = db.query(Supply).filter(Supply.supply_id == supply_id).first()
    if not supply:
        raise HTTPException(status_code=404, detail="Supply item not found")
    return supply


@router.post("", response_model=SupplyRead, status_code=201)
def create_supply(payload: SupplyCreate, db: Session = Depends(get_db)):
    supply = Supply(
        event_id=payload.event_id,
        name=payload.name,
        category=payload.category,
        quantity_start=payload.quantity_start,
        quantity_used=payload.quantity_used or 0,
        quantity_remaining=payload.quantity_remaining,
        expiration_date=payload.expiration_date,
        lot_number=payload.lot_number,
        location=payload.location,
        notes=payload.notes,
    )
    db.add(supply)
    db.commit()
    db.refresh(supply)
    return supply


@router.patch("/{supply_id}", response_model=SupplyRead)
def update_supply(supply_id: str, payload: SupplyUpdate, db: Session = Depends(get_db)):
    supply = db.query(Supply).filter(Supply.supply_id == supply_id).first()
    if not supply:
        raise HTTPException(status_code=404, detail="Supply item not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(supply, field, value)

    # Re-calculate remaining if start and used are present
    if "quantity_start" in update_data or "quantity_used" in update_data:
        supply.quantity_remaining = max(0, supply.quantity_start - supply.quantity_used)

    db.commit()
    db.refresh(supply)
    return supply


@router.delete("/{supply_id}", status_code=204)
def delete_supply(supply_id: str, db: Session = Depends(get_db)):
    supply = db.query(Supply).filter(Supply.supply_id == supply_id).first()
    if not supply:
        raise HTTPException(status_code=404, detail="Supply item not found")
    db.delete(supply)
    db.commit()
    return None
