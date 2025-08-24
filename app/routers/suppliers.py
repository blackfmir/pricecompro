from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.supplier import SupplierOut, SupplierCreate, SupplierUpdate
from app.crud import supplier as crud

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.get("", response_model=list[SupplierOut])
def list_suppliers(db: Session = Depends(get_db)):
    return crud.list_(db)


@router.post("", response_model=SupplierOut, status_code=201)
def create_supplier(payload: SupplierCreate, db: Session = Depends(get_db)):
    return crud.create(db, payload)


@router.put("/{supplier_id}", response_model=SupplierOut)
def update_supplier(supplier_id: int, payload: SupplierUpdate, db: Session = Depends(get_db)):
    obj = crud.update(db, supplier_id, payload)
    if not obj:
        raise HTTPException(404, "Supplier not found")
    return obj


@router.delete("/{supplier_id}")
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    ok = crud.delete(db, supplier_id)
    if not ok:
        raise HTTPException(404, "Supplier not found")
    return {"ok": True}
