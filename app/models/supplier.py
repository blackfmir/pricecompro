
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.supplier_product import SupplierProduct  # noqa: F401

if TYPE_CHECKING:
    from .price_list import PriceList
    from .supplier_product import SupplierProduct


class Supplier(Base):
    __tablename__ = "suppliers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True, unique=True)
    code: Mapped[str | None] = mapped_column(String(64), index=True, unique=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    price_lists: Mapped[list[PriceList]] = relationship(back_populates="supplier")

    supplier_products: Mapped[list[SupplierProduct]] = relationship(
        back_populates="supplier", cascade="all, delete-orphan"
    )

    
