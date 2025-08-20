# app/models/supplier_product.py
from sqlalchemy import (
    String, ForeignKey, Numeric, UniqueConstraint, Date, DateTime, func, JSON, Boolean
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class SupplierProduct(Base):
    __tablename__ = "supplier_products"
    __table_args__ = (
        UniqueConstraint("supplier_id", "supplier_sku", name="uq_supplier_supplier_sku"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id", ondelete="CASCADE"), index=True)
    price_list_id: Mapped[int | None] = mapped_column(ForeignKey("price_lists.id", ondelete="SET NULL"), index=True)
    import_batch_id: Mapped[int | None] = mapped_column(index=True)

    # Ідентифікатори
    supplier_sku: Mapped[str] = mapped_column(String(128), index=True)
    manufacturer_sku: Mapped[str | None] = mapped_column(String(128))
    mpn: Mapped[str | None] = mapped_column(String(128))
    gtin: Mapped[str | None] = mapped_column(String(32), index=True)
    ean: Mapped[str | None] = mapped_column(String(32), index=True)
    upc: Mapped[str | None] = mapped_column(String(32), index=True)
    jan: Mapped[str | None] = mapped_column(String(32), index=True)
    isbn: Mapped[str | None] = mapped_column(String(32), index=True)

    # Назва/виробник/категорії
    name: Mapped[str | None] = mapped_column(String(512))
    brand_raw: Mapped[str | None] = mapped_column(String(128), index=True)
    brand_id: Mapped[int | None] = mapped_column(ForeignKey("manufacturers.id", ondelete="SET NULL"), index=True)
    category_raw: Mapped[str | None] = mapped_column(String(512))
    category_path: Mapped[dict | list | None] = mapped_column(JSON)     # список шляхів/категорій
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), index=True)

    # Ціни/наявність/доставка
    price_raw: Mapped[float | None] = mapped_column(Numeric(18, 2))
    currency_raw: Mapped[str | None] = mapped_column(String(8))
    qty_raw: Mapped[float | None] = mapped_column(Numeric(18, 3))
    availability_text: Mapped[str | None] = mapped_column(String(128))
    delivery_terms: Mapped[str | None] = mapped_column(String(128))
    delivery_date: Mapped[Date | None] = mapped_column(Date)
    location: Mapped[str | None] = mapped_column(String(128))

    # Описи/медіа
    short_description_raw: Mapped[str | None] = mapped_column(String(2000))
    description_raw: Mapped[str | None] = mapped_column(String)          # TEXT
    image_urls: Mapped[list[str] | None] = mapped_column(JSON)           # масив URL

    # Резерв під майбутні опції/атрибути
    attributes_raw: Mapped[dict | None] = mapped_column(JSON)

    # Технічні
    row_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=False), server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=False), onupdate=func.now())

    supplier: Mapped["Supplier"] = relationship(back_populates="supplier_products")
