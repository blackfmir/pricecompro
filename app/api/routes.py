from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.schemas.supplier import SupplierCreate, SupplierOut, SupplierUpdate
from app.schemas.price_list import PriceListCreate, PriceListOut, PriceListUpdate
from app.crud import supplier as supplier_crud
from app.crud import price_list as price_list_crud

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Suppliers
@router.post("/suppliers", response_model=SupplierOut)
def create_supplier(payload: SupplierCreate, db: Session = Depends(get_db)):
    return supplier_crud.create(db, payload)

@router.get("/suppliers", response_model=list[SupplierOut])
def list_suppliers(q: str | None = None, db: Session = Depends(get_db)):
    return supplier_crud.list_(db, q=q)

@router.put("/suppliers/{supplier_id}", response_model=SupplierOut)
def update_supplier(supplier_id: int, payload: SupplierUpdate, db: Session = Depends(get_db)):
    obj = supplier_crud.update(db, supplier_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return obj

@router.delete("/suppliers/{supplier_id}")
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    ok = supplier_crud.delete(db, supplier_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"ok": True}

# Price lists
@router.post("/price-lists", response_model=PriceListOut)
def create_price_list(payload: PriceListCreate, db: Session = Depends(get_db)):
    return price_list_crud.create(db, payload)

@router.get("/price-lists", response_model=list[PriceListOut])
def list_price_lists(supplier_id: int | None = None, db: Session = Depends(get_db)):
    return price_list_crud.list_(db, supplier_id=supplier_id)

@router.put("/price-lists/{pl_id}", response_model=PriceListOut)
def update_price_list(pl_id: int, payload: PriceListUpdate, db: Session = Depends(get_db)):
    obj = price_list_crud.update(db, pl_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Price list not found")
    return obj

@router.delete("/price-lists/{pl_id}")
def delete_price_list(pl_id: int, db: Session = Depends(get_db)):
    ok = price_list_crud.delete(db, pl_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Price list not found")
    return {"ok": True}
