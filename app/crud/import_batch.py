from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from app.models.import_batch import import_batches as IB

def create(db: Session, data: dict) -> IB:
    obj = IB(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update(db: Session, batch_id: int, data: dict) -> IB | None:
    obj = db.get(IB, batch_id)
    if not obj:
        return None
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

def list_(db: Session, *, supplier_id: int | None = None, pricelist_id: int | None = None, limit: int = 200):
    stmt = select(IB).order_by(desc(IB.started_at)).limit(limit)
    if supplier_id is not None:
        stmt = stmt.where(IB.supplier_id == supplier_id)
    if pricelist_id is not None:
        stmt = stmt.where(IB.pricelist_id == pricelist_id)
    return list(db.scalars(stmt).all())
