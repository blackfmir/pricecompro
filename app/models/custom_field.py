from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class custom_fields(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    data_type: Mapped[str] = mapped_column(String(16), default="text")  # text|number|date|bool
    active: Mapped[bool] = mapped_column(Boolean, default=True)
