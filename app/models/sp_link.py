from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class sp_links(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    supplier_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    supplier_sku: Mapped[str] = mapped_column(String(128), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("supplier_id", "supplier_sku", name="uq_sp_link_supplier_sku"),
    )
