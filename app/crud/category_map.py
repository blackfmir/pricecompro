from __future__ import annotations

from typing import Any

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.category_map import CategoryMap
from app.models.supplier_product import SupplierProduct


def list_(db: Session, supplier_id: int) -> list[CategoryMap]:
    return db.query(CategoryMap).filter(CategoryMap.supplier_id == supplier_id).order_by(CategoryMap.raw_name).all()

def create(db: Session, supplier_id: int, raw_name: str, category_id: int) -> CategoryMap:
    obj = CategoryMap(supplier_id=supplier_id, raw_name=raw_name.strip(), category_id=category_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def delete(db: Session, cm_id: int) -> bool:
    obj = db.get(CategoryMap, cm_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True

def suggestions(db: Session, supplier_id: int, limit: int = 100) -> list[dict[str, Any]]:
    rows = (
        db.query(SupplierProduct.category_raw, func.count().label("ct"))
        .filter(
            SupplierProduct.supplier_id == supplier_id,
            SupplierProduct.category_id.is_(None),
            SupplierProduct.category_raw.is_not(None),
            func.trim(SupplierProduct.category_raw) != "",
        )
        .group_by(SupplierProduct.category_raw)
        .order_by(desc("ct"))
        .limit(limit)
        .all()
    )
    return [{"value": r[0], "count": int(r[1])} for r in rows]

def apply_to_products(db: Session, supplier_id: int) -> int:
    maps = list_(db, supplier_id)
    total = 0
    for m in maps:
        total += (
            db.query(SupplierProduct)
            .filter(
                SupplierProduct.supplier_id == supplier_id,
                SupplierProduct.category_id.is_(None),
                SupplierProduct.category_raw == m.raw_name,
            )
            .update({SupplierProduct.category_id: m.category_id}, synchronize_session=False)
        )
    db.commit()
    return total
