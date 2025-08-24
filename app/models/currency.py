from sqlalchemy import Integer, String, Boolean, Float, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class currencies(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    code: Mapped[str] = mapped_column(String(8), unique=True, index=True)   # напр. UAH, PLN, USD
    name: Mapped[str] = mapped_column(String(64))                            # Назва валюти (обов'язково)

    rate_to_base: Mapped[float] = mapped_column(Float, default=1.0)         # курс до базової
    manual_override: Mapped[bool] = mapped_column(Boolean, default=False)    # ручне перевизначення
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    is_base: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    symbol_left: Mapped[str] = mapped_column(String(8), default="")
    symbol_right: Mapped[str] = mapped_column(String(8), default="")
    decimals: Mapped[int] = mapped_column(Integer, default=2)

    updated_at: Mapped["DateTime"] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
