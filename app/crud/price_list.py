from sqlalchemy.orm import Session

from app.crud.currency import get_primary
from app.models.price_list import PriceList
from app.schemas.price_list import PriceListCreate, PriceListUpdate


def create(db: Session, payload: PriceListCreate) -> PriceList:
    data = payload.model_dump()
    if data.get("default_currency_id") is None:
        cur = get_primary(db)
        if cur:
            data["default_currency_id"] = cur.id
    obj = PriceList(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def get(db: Session, price_list_id: int) -> PriceList | None:
    return db.get(PriceList, price_list_id)

def list_(db: Session, supplier_id: int | None = None) -> list[PriceList]:
    query = db.query(PriceList)
    if supplier_id is not None:
        query = query.filter(PriceList.supplier_id == supplier_id)
    return query.order_by(PriceList.id.desc()).all()

def update(db: Session, price_list_id: int, data: PriceListUpdate) -> PriceList | None:
    obj = db.get(PriceList, price_list_id)
    if not obj:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj

def delete(db: Session, price_list_id: int) -> bool:
    obj = db.get(PriceList, price_list_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
