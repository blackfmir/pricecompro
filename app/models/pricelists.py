from sqlalchemy import Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class pricelists(Base):  # таблиця: pricelists
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id", ondelete="RESTRICT"), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)

    # local|http|ftp|parser
    source_type: Mapped[str] = mapped_column(String(16), default="local")
    # xlsx|csv|xml|json|html
    format: Mapped[str] = mapped_column(String(16), default="xlsx")

    # Зберігаємо як JSON-рядки (у SQLite TEXT). На етапі імпорту будемо парсити.
    source_config: Mapped[str | None] = mapped_column(Text, default=None)
    mapping: Mapped[str | None] = mapped_column(Text, default=None)

    active: Mapped[bool] = mapped_column(Boolean, default=True)
