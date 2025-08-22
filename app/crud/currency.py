from __future__ import annotations

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.currency import Currency
from app.models.price_list import PriceList
from app.schemas.currency import CurrencyCreate, CurrencyUpdate


def list_(db: Session, q: str | None = None) -> list[Currency]:
    stmt = select(Currency)
    if q:
        like = f"%{q}%"
        stmt = stmt.where((Currency.name.ilike(like)) | (Currency.iso_code.ilike(like)))
    return list(db.scalars(stmt).all())

def get(db: Session, currency_id: int) -> Currency | None:
    return db.get(Currency, currency_id)

def create(db: Session, payload: CurrencyCreate) -> Currency:
    obj = Currency(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_(db: Session, currency_id: int, payload: CurrencyUpdate) -> Currency | None:
    obj = get(db, currency_id)
    if not obj:
        return None
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

def delete(db: Session, currency_id: int) -> tuple[bool, str | None]:
    obj = get(db, currency_id)
    if not obj:
        return False, "Currency not found"
    if obj.is_primary:
        return False, "Cannot delete the primary currency"
    in_use = db.scalar(
        select(func.count()).select_from(PriceList).where(PriceList.default_currency_id == currency_id)
    )
    if in_use and in_use > 0:
        return False, f"Currency is used in {in_use} price list(s)"
    db.delete(obj)
    db.commit()
    return True, None

def set_primary(db: Session, currency_id: int) -> Currency | None:
    obj = get(db, currency_id)
    if not obj:
        return None
    # скидаємо прапор у всіх, ставимо для однієї
    db.execute(update(Currency).values(is_primary=False))
    obj.is_primary = True
    db.commit()
    db.refresh(obj)
    return obj

def get_primary(db: Session) -> Currency | None:
    return db.scalars(select(Currency).where(Currency.is_primary == True)).first()  # noqa: E712
