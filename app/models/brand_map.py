from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class BrandMap(Base):
    __tablename__ = "brand_maps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id", ondelete="CASCADE"), index=True)
    raw_name: Mapped[str] = mapped_column(String(255))
    manufacturer_id: Mapped[int] = mapped_column(ForeignKey("manufacturers.id"), index=True)

    supplier = relationship("Supplier")
    manufacturer = relationship("Manufacturer")

    __table_args__ = (UniqueConstraint("supplier_id", "raw_name", name="uq_brand_map_supplier_raw"),)
