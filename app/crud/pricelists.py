from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.pricelists import pricelists
from app.schemas.pricelists import PricelistCreate, PricelistUpdate


def list_(db: Session) -> list[pricelists]:
    return list(db.scalars(select(pricelists).order_by(pricelists.id.desc())).all())


def get(db: Session, pr_id: int) -> pricelists | None:
    return db.get(pricelists, pr_id)


def create(db: Session, data: PricelistCreate) -> pricelists:
    obj = pricelists(
        supplier_id=data.supplier_id,
        name=data.name,
        source_type=data.source_type,
        format=data.format,
        source_config=data.source_config,
        mapping=data.mapping,
        active=data.active,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, pr_id: int, data: PricelistUpdate) -> pricelists | None:
    obj = get(db, pr_id)
    if not obj:
        return None

    if data.supplier_id is not None:
        obj.supplier_id = data.supplier_id
    if data.name is not None:
        obj.name = data.name
    if data.source_type is not None:
        obj.source_type = data.source_type
    if data.format is not None:
        obj.format = data.format
    if data.source_config is not None:
        obj.source_config = data.source_config
    if data.mapping is not None:
        obj.mapping = data.mapping
    if data.active is not None:
        obj.active = data.active

    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, pr_id: int) -> bool:
    obj = get(db, pr_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
