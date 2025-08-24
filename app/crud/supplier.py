from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.supplier import suppliers
from app.schemas.supplier import SupplierCreate, SupplierUpdate


def list_(db: Session) -> list[suppliers]:
    return list(db.scalars(select(suppliers).order_by(suppliers.id.desc())).all())


def get(db: Session, supplier_id: int) -> suppliers | None:
    return db.get(suppliers, supplier_id)


def create(db: Session, data: SupplierCreate) -> suppliers:
    obj = suppliers(name=data.name, code=data.code, active=data.active)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, supplier_id: int, data: SupplierUpdate) -> suppliers | None:
    obj = get(db, supplier_id)
    if not obj:
        return None

    if data.name is not None:
        obj.name = data.name
    if data.code is not None:
        obj.code = data.code
    if data.active is not None:
        obj.active = data.active

    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, supplier_id: int) -> bool:
    obj = get(db, supplier_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
