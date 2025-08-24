# app/services/money.py
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Any, Mapping

from sqlalchemy.orm import Session
from app.crud import currency as currency_crud


@dataclass(frozen=True)
class CurrencyFmt:
    code: str
    symbol_left: str
    symbol_right: str
    decimals: int


def _to_decimal(val: Any) -> Decimal:
    if isinstance(val, Decimal):
        return val
    try:
        return Decimal(str(val))
    except InvalidOperation:
        raise ValueError(f"Невірна числова сума: {val!r}")


def get_currency_map(db: Session) -> dict[str, CurrencyFmt]:
    """
    Зчитує довідник валют і повертає компактну мапу для форматування/конвертації.
    """
    cmap: dict[str, CurrencyFmt] = {}
    for c in currency_crud.list_(db):
        cmap[c.code.upper()] = CurrencyFmt(
            code=c.code.upper(),
            symbol_left=c.symbol_left or "",
            symbol_right=c.symbol_right or "",
            decimals=int(c.decimals or 2),
        )
    return cmap


def _quantize(amount: Decimal, decimals: int) -> Decimal:
    if decimals < 0:
        decimals = 0
    q = Decimal("1").scaleb(-decimals)  # 10 ** -decimals
    return amount.quantize(q, rounding=ROUND_HALF_UP)


def _fmt_number(amount: Decimal, decimals: int) -> str:
    # тисячні розділювачі: кома, десятковий — крапка (поки без локалізації)
    return f"{amount:,.{decimals}f}"


def format_money(
    amount: Any,
    *,
    currency_code: str,
    db: Session | None = None,
    cmap: Mapping[str, CurrencyFmt] | None = None,
) -> str:
    """
    Повертає рядок суми з урахуванням символів зліва/справа та кількості знаків.
    Можна передати або `db`, або вже підготовлену `cmap` (швидше для шаблонів).
    """
    if cmap is None:
        if db is None:
            raise ValueError("Потрібен або db, або currency_map (cmap).")
        cmap = get_currency_map(db)

    cur = cmap.get(currency_code.upper())
    if cur is None:
        # fallback: 2 знаки, без символів
        dec = _quantize(_to_decimal(amount), 2)
        return _fmt_number(dec, 2)

    dec_amount = _quantize(_to_decimal(amount), cur.decimals)
    num = _fmt_number(dec_amount, cur.decimals)

    # мінус завжди перед лівим символом
    negative = num.startswith("-")
    if negative:
        num = num[1:]  # приберемо "-", додамо самі

    left = cur.symbol_left or ""
    right = cur.symbol_right or ""

    # якщо є правий символ — вставимо пробіл між числом і символом
    s = f"{left}{num}" + (f" {right}" if right else "")
    return f"-{s}" if negative else s


def convert(amount: Any, code_from: str, code_to: str, db: Session) -> Decimal:
    """
    Конвертація через відношення курсів, незалежно від «базової».
    amount_in_to = amount * (rate_from / rate_to)
    """
    rate_map = {c.code.upper(): Decimal(str(c.rate_to_base)) for c in currency_crud.list_(db)}
    rf = rate_map.get(code_from.upper())
    rt = rate_map.get(code_to.upper())
    if rf is None or rt is None:
        raise ValueError("Невідома валюта для конвертації")
    return _to_decimal(amount) * (rf / rt)


# ---- Jinja filter ----
def jinja_money_filter(value: Any, code: str, cmap: Mapping[str, CurrencyFmt]) -> str:
    """
    Використання у шаблоні: {{ 1234.5 | money('PLN', currency_map) }}
    """
    return format_money(value, currency_code=code, cmap=cmap)
