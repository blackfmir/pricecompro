from pydantic import BaseModel, Field
from typing import Any

class ScraperBase(BaseModel):
    supplier_id: int
    name: str = Field(min_length=1, max_length=128)
    start_urls: list[str] = []
    settings: dict[str, Any] = {}
    rules: dict[str, Any] = {}
    active: bool = True
    pricelist_id: int | None = None

class ScraperCreate(ScraperBase):
    pass

class ScraperUpdate(BaseModel):
    name: str | None = None
    start_urls: list[str] | None = None
    settings: dict | None = None
    rules: dict | None = None
    active: bool | None = None
    pricelist_id: int | None = None

class ScraperOut(ScraperBase):
    id: int
    class Config:
        from_attributes = True
