from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.pricelists import PricelistOut, PricelistCreate, PricelistUpdate
from app.crud import pricelists as crud

router = APIRouter(prefix="/pricelists", tags=["pricelists"])


@router.get("", response_model=list[PricelistOut])
def list_pricelists(db: Session = Depends(get_db)):
    return crud.list_(db)


@router.post("", response_model=PricelistOut, status_code=201)
def create_pricelist(payload: PricelistCreate, db: Session = Depends(get_db)):
    return crud.create(db, payload)


@router.put("/{pr_id}", response_model=PricelistOut)
def update_pricelist(pr_id: int, payload: PricelistUpdate, db: Session = Depends(get_db)):
    obj = crud.update(db, pr_id, payload)
    if not obj:
        raise HTTPException(404, "Pricelist not found")
    return obj


@router.delete("/{pr_id}")
def delete_pricelist(pr_id: int, db: Session = Depends(get_db)):
    ok = crud.delete(db, pr_id)
    if not ok:
        raise HTTPException(404, "Pricelist not found")
    return {"ok": True}
