from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base

if TYPE_CHECKING:
    from .price_list import PriceList
    from .supplier import Supplier


class SupplierProduct(Base):
    __tablename__ = "supplier_products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), index=True)
    price_list_id: Mapped[int | None] = mapped_column(ForeignKey("price_lists.id"), nullable=True, index=True)
    import_batch_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Ідентифікатори
    supplier_sku: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    manufacturer_sku: Mapped[str | None] = mapped_column(String(128), nullable=True)
    mpn: Mapped[str | None] = mapped_column(String(128), nullable=True)
    gtin: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ean: Mapped[str | None] = mapped_column(String(32), nullable=True)
    upc: Mapped[str | None] = mapped_column(String(32), nullable=True)
    jan: Mapped[str | None] = mapped_column(String(32), nullable=True)
    isbn: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Основні дані
    name: Mapped[str | None] = mapped_column(String(300), index=True, nullable=True)
    brand_raw: Mapped[str | None] = mapped_column(String(128), nullable=True)
    brand_id: Mapped[int | None] = mapped_column(ForeignKey("manufacturers.id"), nullable=True)
    category_raw: Mapped[str | None] = mapped_column(String(255), nullable=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    location: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Ціни / валюта / кількість / доступність
    price_raw: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency_raw: Mapped[str | None] = mapped_column(String(8), nullable=True)
    qty_raw: Mapped[float | None] = mapped_column(Float, nullable=True)
    availability_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    delivery_terms: Mapped[str | None] = mapped_column(String(255), nullable=True)
    delivery_date: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Опис і фото
    short_description_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_urls: Mapped[str | None] = mapped_column(Text, nullable=True)  # зберігаємо як JSON-рядок

    # Службові
    row_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=False), server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now())

    # Зв’язки
    supplier: Mapped[Supplier] = relationship(back_populates="supplier_products")
    price_list: Mapped[PriceList] = relationship(back_populates="supplier_products")
