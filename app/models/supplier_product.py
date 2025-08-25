from sqlalchemy import Integer, String, Boolean, Float, DateTime, func, Index, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class supplier_products(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    supplier_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    pricelist_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    supplier_sku: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(512), nullable=False)

    price_raw: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency_raw: Mapped[str | None] = mapped_column(String(8), nullable=True)
    availability_raw: Mapped[str | None] = mapped_column(String(64), nullable=True)

    manufacturer_raw: Mapped[str | None] = mapped_column(String(128), nullable=True)
    manufacturer_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    category_raw: Mapped[str | None] = mapped_column(String(128), nullable=True)
    category_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped["DateTime"] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped["DateTime"] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    extra_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # довільні додаткові атрибути

    __table_args__ = (
        Index("uq_sup_prod_supplier_sku", "supplier_id", "supplier_sku", unique=True),
    )
