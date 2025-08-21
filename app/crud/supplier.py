from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.price_list import PriceList
from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierUpdate
from app.utils.slug import slugify_code


def _exists_code(db: Session, code: str, exclude_id: int | None = None) -> bool:
    q = db.query(Supplier.id).filter(Supplier.code == code)
    if exclude_id is not None:
        q = q.filter(Supplier.id != exclude_id)
    return q.count() > 0

def _ensure_unique_code(db: Session, base: str, supplier_id: int | None = None) -> str:
    code = base or "supplier"
    if not _exists_code(db, code, exclude_id=supplier_id):
        return code
    i = 2
    while True:
        cand = f"{code}-{i}"
        if not _exists_code(db, cand, exclude_id=supplier_id):
            return cand
        i += 1

def create(db: Session, payload: SupplierCreate) -> Supplier:
    code = (payload.code or "").strip() or slugify_code(payload.name)
    code = _ensure_unique_code(db, code)
    obj = Supplier(name=payload.name, code=code, active=payload.active)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def list_(db: Session, q: str | None = None) -> list[Supplier]:
    query = db.query(Supplier)
    if q:
        like = f"%{q.strip().lower()}%"
        query = query.filter(
            func.lower(Supplier.name).like(like) | func.lower(Supplier.code).like(like)
        )
    return query.order_by(Supplier.name).all()

def update(db: Session, supplier_id: int, payload: SupplierUpdate) -> Supplier | None:
    obj = db.get(Supplier, supplier_id)
    if not obj:
        return None
    if payload.name is not None:
        obj.name = payload.name
    if payload.active is not None:
        obj.active = payload.active
    if payload.code is not None:
        new_code = (payload.code or "").strip()
        if not new_code and payload.name:
            new_code = slugify_code(payload.name)
        if new_code:
            obj.code = _ensure_unique_code(db, new_code, supplier_id=obj.id)
    db.commit()
    db.refresh(obj)
    return obj

def can_delete(db: Session, supplier_id: int) -> tuple[bool, str | None]:
    obj = db.get(Supplier, supplier_id)
    if not obj:
        return False, "not_found"
    cnt = db.query(PriceList).filter(PriceList.supplier_id == supplier_id).count()
    if cnt > 0:
        return False, "has_price_lists"
    return True, None

def delete(db: Session, supplier_id: int) -> tuple[bool, str | None]:
    ok, reason = can_delete(db, supplier_id)
    if not ok:
        return False, reason
    obj = db.get(Supplier, supplier_id)
    db.delete(obj)
    db.commit()
    return True, None
