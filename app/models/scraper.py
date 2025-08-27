from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class scrapers(Base):
    __tablename__ = "scrapers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)

    pricelist_id = Column(Integer, ForeignKey("pricelists.id"), nullable=True)

    settings_json = Column(Text, default="{}")
    rules_json = Column(Text, default="{}")
    start_urls_json = Column(Text, default="[]")  # ← ДОДАТИ
