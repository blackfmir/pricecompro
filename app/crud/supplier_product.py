# app/crud/supplier_product.py
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.supplier_product import SupplierProduct
from app.schemas.supplier_product import (
    SupplierProductCreate,
    SupplierProductUpdate,
)


def upsert_many(db: Session, items: list[SupplierProductCreate]) -> dict:
    inserted = 0
    updated = 0
    for it in items:
        obj = (
            db.query(SupplierProduct)
            .filter(
                and_(
                    SupplierProduct.supplier_id == it.supplier_id,
                    SupplierProduct.supplier_sku == it.supplier_sku,
                )
            )
            .first()
        )
        if obj:
            for f, v in it.model_dump().items():
                if f in {"supplier_id", "supplier_sku"}:
                    continue
                setattr(obj, f, v)
            updated += 1
        else:
            db.add(SupplierProduct(**it.model_dump()))
            inserted += 1
    db.commit()
    return {"inserted": inserted, "updated": updated}


def list_(
    db: Session,
    supplier_id: int | None = None,
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    query = db.query(SupplierProduct)
    if supplier_id is not None:
        query = query.filter(SupplierProduct.supplier_id == supplier_id)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (SupplierProduct.name.ilike(like))
            | (SupplierProduct.supplier_sku.ilike(like))
        )
    total = query.count()
    rows = (
        query.order_by(SupplierProduct.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {"total": total, "items": rows}


def update(db: Session, sp_id: int, data: SupplierProductUpdate):
    obj = db.get(SupplierProduct, sp_id)
    if not obj:
        return None
    for f, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, f, v)
    db.commit()
    db.refresh(obj)
    return obj
