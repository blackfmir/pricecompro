from __future__ import annotations

from pydantic import BaseModel


class SuggestionOut(BaseModel):
    value: str
    count: int

class BrandMapCreate(BaseModel):
    supplier_id: int
    raw_name: str
    manufacturer_id: int

class BrandMapOut(BrandMapCreate):
    id: int

class CategoryMapCreate(BaseModel):
    supplier_id: int
    raw_name: str
    category_id: int

class CategoryMapOut(CategoryMapCreate):
    id: int
