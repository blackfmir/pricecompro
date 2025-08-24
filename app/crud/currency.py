from sqlalchemy import select, func, update as sa_update
from sqlalchemy.orm import Session
from app.models.currency import currencies
from app.schemas.currency import CurrencyCreate, CurrencyUpdate


def list_(db: Session) -> list[currencies]:
    return list(db.scalars(select(currencies).order_by(currencies.code.asc())).all())


def get(db: Session, currency_id: int) -> currencies | None:
    return db.get(currencies, currency_id)


def get_base(db: Session) -> currencies | None:
    return db.scalar(select(currencies).where(currencies.is_base.is_(True)))


def create(db: Session, data: CurrencyCreate) -> currencies:
    total = db.scalar(select(func.count()).select_from(currencies)) or 0
    obj = currencies(
        code=data.code,
        name=data.name,
        rate_to_base=data.rate_to_base,
        manual_override=data.manual_override,
        active=data.active,
        is_base=(total == 0),
        symbol_left=data.symbol_left or "",
        symbol_right=data.symbol_right or "",
        decimals=data.decimals,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)

    return obj


def update(db: Session, currency_id: int, data: CurrencyUpdate) -> currencies | None:
    obj = get(db, currency_id)
    if not obj:
        return None

    if data.code is not None:
        obj.code = data.code
    if data.name is not None:
        obj.name = data.name
    if data.rate_to_base is not None:
        obj.rate_to_base = data.rate_to_base
    if data.manual_override is not None:
        obj.manual_override = data.manual_override
    if data.active is not None:
        obj.active = data.active
    if data.symbol_left is not None:
        obj.symbol_left = data.symbol_left
    if data.symbol_right is not None:
        obj.symbol_right = data.symbol_right
    if data.decimals is not None:
        obj.decimals = data.decimals

    db.commit()
    db.refresh(obj)

    return obj


def delete(db: Session, currency_id: int) -> bool:
    obj = get(db, currency_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


def set_base(db: Session, currency_id: int) -> currencies | None:
    obj = get(db, currency_id)
    if not obj:
        return None
    db.execute(sa_update(currencies).values(is_base=False))
    obj.is_base = True
    # курс НЕ змінюємо
    db.commit()
    db.refresh(obj)
    return obj
