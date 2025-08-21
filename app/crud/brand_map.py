from __future__ import annotations

from typing import Any

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.brand_map import BrandMap
from app.models.supplier_product import SupplierProduct


def list_(db: Session, supplier_id: int) -> list[BrandMap]:
    return db.query(BrandMap).filter(BrandMap.supplier_id == supplier_id).order_by(BrandMap.raw_name).all()

def create(db: Session, supplier_id: int, raw_name: str, manufacturer_id: int) -> BrandMap:
    obj = BrandMap(supplier_id=supplier_id, raw_name=raw_name.strip(), manufacturer_id=manufacturer_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def delete(db: Session, bm_id: int) -> bool:
    obj = db.get(BrandMap, bm_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True

def update(db: Session, bm_id: int, manufacturer_id: int) -> BrandMap | None:
    obj = db.get(BrandMap, bm_id)
    if not obj:
        return None
    obj.manufacturer_id = manufacturer_id
    db.commit()
    db.refresh(obj)
    return obj


def suggestions(db: Session, supplier_id: int, limit: int = 100) -> list[dict[str, Any]]:
    rows = (
        db.query(SupplierProduct.brand_raw, func.count().label("ct"))
        .filter(
            SupplierProduct.supplier_id == supplier_id,
            SupplierProduct.brand_id.is_(None),
            SupplierProduct.brand_raw.is_not(None),
            func.trim(SupplierProduct.brand_raw) != "",
        )
        .group_by(SupplierProduct.brand_raw)
        .order_by(desc("ct"))
        .limit(limit)
        .all()
    )
    return [{"value": r[0], "count": int(r[1])} for r in rows]

def apply_to_products(db: Session, supplier_id: int) -> int:
    """Проставляє brand_id у supplier_products по існуючих мапах. Повертає кількість оновлених рядків."""
    maps = list_(db, supplier_id)
    total = 0
    for m in maps:
        total += (
            db.query(SupplierProduct)
            .filter(
                SupplierProduct.supplier_id == supplier_id,
                SupplierProduct.brand_id.is_(None),
                SupplierProduct.brand_raw == m.raw_name,
            )
            .update({SupplierProduct.brand_id: m.manufacturer_id}, synchronize_session=False)
        )
    db.commit()
    return total
