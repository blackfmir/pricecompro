from sqlalchemy.orm import Session

from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierUpdate


def create(db: Session, data: SupplierCreate) -> Supplier:
    obj = Supplier(name=data.name, code=data.code, active=data.active)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def get(db: Session, supplier_id: int) -> Supplier | None:
    return db.get(Supplier, supplier_id)

def list_(db: Session, q: str | None = None) -> list[Supplier]:
    query = db.query(Supplier)
    if q:
        query = query.filter(Supplier.name.ilike(f"%{q}%"))
    return query.order_by(Supplier.name).all()

def update(db: Session, supplier_id: int, data: SupplierUpdate) -> Supplier | None:
    obj = db.get(Supplier, supplier_id)
    if not obj:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
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
