from sqlalchemy import String, ForeignKey, Enum, JSON, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum
from app.models.base import Base
from typing import List
from app.models.supplier_product import SupplierProduct  # noqa: F401

class SourceType(str, enum.Enum):
    local = "local"
    ftp = "ftp"
    http = "http"
    parser = "parser"

class PriceList(Base):
    __tablename__ = "price_lists"
    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("supplier.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType), default=SourceType.local)
    source_config: Mapped[dict | None] = mapped_column(JSON, default=None)
    format: Mapped[str | None] = mapped_column(String(32), default="csv")
    mapping: Mapped[dict | None] = mapped_column(JSON, default=None)
    schedule: Mapped[str | None] = mapped_column(String(128), default=None)  # cron як рядок, заглушка
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)
    last_status: Mapped[str | None] = mapped_column(String(64), default=None)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    supplier: Mapped["Supplier"] = relationship(back_populates="price_lists")

    supplier_products: Mapped[list["SupplierProduct"]] = relationship(
        back_populates="price_list"
    )
