from typing import Iterable
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
from app.models.supplier_product import supplier_products as SP
from app.schemas.supplier_product import SupplierProductCreate, SupplierProductUpdate

def list_(
    db: Session,
    *,
    supplier_id: int | None = None,
    pricelist_id: int | None = None,
    q: str | None = None,
    limit: int = 200,
):
    stmt = select(SP).order_by(SP.updated_at.desc()).limit(limit)
    if supplier_id is not None:
        stmt = stmt.where(SP.supplier_id == supplier_id)
    if pricelist_id is not None:
        stmt = stmt.where(SP.pricelist_id == pricelist_id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where((SP.supplier_sku.ilike(like)) | (SP.name.ilike(like)))
    return list(db.scalars(stmt).all())

def get(db: Session, sp_id: int) -> SP | None:
    return db.get(SP, sp_id)

def upsert_many(
    db: Session,
    *,
    supplier_id: int,
    pricelist_id: int,
    items: Iterable[dict],
) -> dict:
    """Upsert по (supplier_id, supplier_sku). Повертає статистику."""
    items = list(items)
    if not items:
        return {"inserted": 0, "updated": 0}

    skus = [str(i.get("supplier_sku", "")).strip() for i in items if i.get("supplier_sku")]
    existing = {}
    if skus:
        stmt = select(SP).where(SP.supplier_id == supplier_id, SP.supplier_sku.in_(skus))
        for row in db.scalars(stmt):
            existing[row.supplier_sku] = row

    ins, upd = 0, 0
    for it in items:
        sku = str(it.get("supplier_sku", "")).strip()
        name = str(it.get("name", "")).strip()
        if not sku or not name:
            continue  # пропускаємо брак даних

        target = existing.get(sku)
        if target is None:
            target = SP(
                supplier_id=supplier_id,
                pricelist_id=pricelist_id,
                supplier_sku=sku,
                name=name,
                price_raw=it.get("price_raw"),
                currency_raw=it.get("currency_raw"),
                availability_raw=it.get("availability_raw"),
                manufacturer_raw=it.get("manufacturer_raw"),
                category_raw=it.get("category_raw"),
                is_active=True,
            )
            db.add(target)
            ins += 1
        else:
            target.pricelist_id = pricelist_id
            target.name = name
            target.price_raw = it.get("price_raw")
            target.currency_raw = it.get("currency_raw")
            target.availability_raw = it.get("availability_raw")
            target.manufacturer_raw = it.get("manufacturer_raw")
            target.category_raw = it.get("category_raw")
            upd += 1

    db.commit()
    return {"inserted": ins, "updated": upd}

def update(db: Session, sp_id: int, data: SupplierProductUpdate) -> SP | None:
    obj = get(db, sp_id)
    if not obj:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj

def delete(db: Session, sp_id: int) -> bool:
    obj = get(db, sp_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True

def list_paged(
    db: Session,
    *,
    supplier_id: int | None = None,
    pricelist_id: int | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 30,
):
    conds = []
    if supplier_id is not None:
        conds.append(SP.supplier_id == supplier_id)
    if pricelist_id is not None:
        conds.append(SP.pricelist_id == pricelist_id)
    if q:
        like = f"%{q}%"
        conds.append((SP.supplier_sku.ilike(like)) | (SP.name.ilike(like)))
    where_expr = and_(*conds) if conds else None

    # total
    total_stmt = select(func.count()).select_from(SP)
    if where_expr is not None:
        total_stmt = total_stmt.where(where_expr)
    total = db.scalar(total_stmt) or 0

    # page data
    offset = max(0, (page - 1) * page_size)
    stmt = select(SP).order_by(SP.updated_at.desc()).offset(offset).limit(page_size)
    if where_expr is not None:
        stmt = stmt.where(where_expr)
    items = list(db.scalars(stmt).all())
    return items, int(total)
