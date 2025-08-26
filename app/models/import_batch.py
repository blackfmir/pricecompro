from sqlalchemy import Integer, String, Boolean, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class import_batches(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    supplier_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    pricelist_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    started_at: Mapped["DateTime"] = mapped_column(DateTime, server_default=func.now())
    finished_at: Mapped["DateTime"] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    source_path: Mapped[str | None] = mapped_column(Text, nullable=True)     # відносний шлях у storage
    format: Mapped[str | None] = mapped_column(String(16), nullable=True)    # csv|xlsx|xml
    ok: Mapped[bool] = mapped_column(Boolean, default=True)
    message: Mapped[str | None] = mapped_column(String(255), nullable=True)

    inserted: Mapped[int] = mapped_column(Integer, default=0)
    updated: Mapped[int] = mapped_column(Integer, default=0)
    skipped: Mapped[int] = mapped_column(Integer, default=0)
    warnings: Mapped[int] = mapped_column(Integer, default=0)

    errors_url: Mapped[str | None] = mapped_column(Text, nullable=True)      # публічний URL на CSV помилок
    mapping_json: Mapped[str | None] = mapped_column(Text, nullable=True)    # snapshot мапінгу (JSON)
