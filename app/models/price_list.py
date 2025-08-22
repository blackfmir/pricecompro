from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from .currency import Currency
    from .supplier import Supplier
    from .supplier_product import SupplierProduct


class SourceType(str, enum.Enum):
    local = "local"
    ftp = "ftp"
    http = "http"
    parser = "parser"


class PriceList(Base):
    __tablename__ = "price_lists"

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200))
    source_type: Mapped[SourceType] = mapped_column(SAEnum(SourceType), default=SourceType.local)
    source_config: Mapped[dict | None] = mapped_column(JSON, default=None)
    format: Mapped[str | None] = mapped_column(String(32), default="csv")
    mapping: Mapped[dict | None] = mapped_column(JSON, default=None)
    schedule: Mapped[str | None] = mapped_column(String(128), default=None)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)
    last_status: Mapped[str | None] = mapped_column(String(64), default=None)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Валюта за замовчуванням для цього прайсу
    default_currency_id: Mapped[int | None] = mapped_column(ForeignKey("currencies.id"), nullable=True)
    default_currency: Mapped[Currency | None] = relationship(back_populates="price_lists")

    # Дзеркало до SupplierProduct.price_list
    supplier_products: Mapped[list[SupplierProduct]] = relationship(
        back_populates="price_list",
        cascade="all,delete-orphan",
    )

    # Постачальник
    supplier: Mapped[Supplier] = relationship(back_populates="price_lists")
