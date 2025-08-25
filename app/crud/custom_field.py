from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.custom_field import custom_fields as CF
from app.schemas.custom_field import CustomFieldCreate, CustomFieldUpdate

def list_(db: Session, *, active_only: bool = True):
    stmt = select(CF).order_by(CF.name.asc())
    if active_only:
        stmt = stmt.where(CF.active == True)  # noqa: E712
    return list(db.scalars(stmt).all())

def get(db: Session, cf_id: int) -> CF | None:
    return db.get(CF, cf_id)

def get_by_code(db: Session, code: str) -> CF | None:
    stmt = select(CF).where(CF.code == code)
    return db.scalars(stmt).first()

def create(db: Session, data: CustomFieldCreate) -> CF:
    obj = CF(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update(db: Session, cf_id: int, data: CustomFieldUpdate) -> CF | None:
    obj = get(db, cf_id)
    if not obj:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

def delete(db: Session, cf_id: int) -> bool:
    obj = get(db, cf_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
