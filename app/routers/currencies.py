from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.currency import CurrencyOut, CurrencyCreate, CurrencyUpdate
from app.crud import currency as crud

router = APIRouter(prefix="/currencies", tags=["currencies"])

@router.get("", response_model=list[CurrencyOut])
def list_currencies(db: Session = Depends(get_db)):
    return crud.list_(db)

@router.post("", response_model=CurrencyOut, status_code=201)
def create_currency(payload: CurrencyCreate, db: Session = Depends(get_db)):
    return crud.create(db, payload)

@router.put("/{currency_id}", response_model=CurrencyOut)
def update_currency(currency_id: int, payload: CurrencyUpdate, db: Session = Depends(get_db)):
    obj = crud.update(db, currency_id, payload)
    if not obj:
        raise HTTPException(404, "Currency not found")
    return obj

@router.delete("/{currency_id}")
def delete_currency(currency_id: int, db: Session = Depends(get_db)):
    ok = crud.delete(db, currency_id)
    if not ok:
        raise HTTPException(404, "Currency not found")
    return {"ok": True}
