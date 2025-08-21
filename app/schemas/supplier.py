from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class SupplierBase(BaseModel):
    name: str
    code: str | None = None
    active: bool = True

class SupplierCreate(SupplierBase):
    pass

class SupplierUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    active: bool | None = None

class SupplierOut(SupplierBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
