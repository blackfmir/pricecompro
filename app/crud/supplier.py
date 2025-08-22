from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierUpdate


def create(db: Session, payload: SupplierCreate) -> Supplier:
    obj = Supplier(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_(db: Session, q: str | None = None) -> list[Supplier]:
    query = db.query(Supplier)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Supplier.name.ilike(like),
                Supplier.code.ilike(like),
            )
        )
    return list(query.order_by(Supplier.name).all())


def update(db: Session, supplier_id: int, payload: SupplierUpdate) -> Supplier | None:
    obj = db.get(Supplier, supplier_id)
    if not obj:
        return None
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, supplier_id: int) -> bool:
    obj = db.get(Supplier, supplier_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
