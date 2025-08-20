from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Supplier(Base):
    __tablename__ = "suppliers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True, unique=True)
    code: Mapped[str | None] = mapped_column(String(64), index=True, unique=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    price_lists: Mapped[list["PriceList"]] = relationship(back_populates="supplier")
