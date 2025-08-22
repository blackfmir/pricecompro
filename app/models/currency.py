from __future__ import annotations

from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Currency(Base):
    __tablename__ = "currencies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    iso_code: Mapped[str] = mapped_column(String(3), unique=True, index=True)
    symbol_left: Mapped[str | None] = mapped_column(String(8), nullable=True)
    symbol_right: Mapped[str | None] = mapped_column(String(8), nullable=True)
    decimals: Mapped[int] = mapped_column(Integer, default=2)
    rate: Mapped[float] = mapped_column(Float, default=1.0)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)  # лише одна True
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    price_lists: Mapped[list[PriceList]] = relationship(back_populates="default_currency")
