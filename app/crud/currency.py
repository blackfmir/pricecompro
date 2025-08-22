from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.currency import Currency
from app.models.price_list import PriceList  # ДОДАЙ ЦЕ
from app.schemas.currency import CurrencyCreate, CurrencyUpdate


def list_(db: Session, q: str | None = None) -> list[Currency]:
    stmt = select(Currency)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            (Currency.name.ilike(like)) | (Currency.iso_code.ilike(like))
        )
    return list(db.execute(stmt).scalars().all())


def get(db: Session, currency_id: int) -> Currency | None:
    return db.get(Currency, currency_id)


def create(db: Session, payload: CurrencyCreate) -> Currency:
    obj = Currency(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_(db: Session, currency_id: int, payload: CurrencyUpdate) -> Currency | None:
    obj = db.get(Currency, currency_id)
    if not obj:
        return None
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, currency_id: int) -> bool:
    obj = db.get(Currency, currency_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


# НОВЕ: безпечне видалення з перевірками (is_primary та використання у прайс-листах)
def delete_safe(db: Session, currency_id: int) -> tuple[bool, str | None]:
    obj = db.get(Currency, currency_id)
    if not obj:
        return False, "Currency not found"

    if obj.is_primary:
        return False, "Cannot delete primary currency"

    in_use = (
        db.query(PriceList)
        .filter(PriceList.default_currency_id == currency_id)
        .count()
    )
    if in_use:
        return False, f"Currency is used by {in_use} price list(s)"

    db.delete(obj)
    db.commit()
    return True, None

def get_primary(db: Session) -> Currency | None:
    """Повертає поточну основну валюту або None."""
    stmt = select(Currency).where(Currency.is_primary.is_(True))
    return db.execute(stmt).scalars().first()


def set_primary(db: Session, currency_id: int) -> Currency | None:
    """Робить валюту основною (скидаючи прапорець у всіх інших)."""
    obj = db.get(Currency, currency_id)
    if not obj:
        return None

    # скидаємо поточну основну, якщо є
    db.query(Currency).filter(Currency.is_primary.is_(True)).update(
        {Currency.is_primary: False}
    )
    # ставимо нову основну
    obj.is_primary = True
    db.commit()
    db.refresh(obj)
    return obj

