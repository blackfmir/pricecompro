# app/schemas/supplier.py
from pydantic import BaseModel, Field, field_validator


class SupplierBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=64)  # обов'язковий
    active: bool = True

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Код не може бути порожнім")
        return v


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    code: str | None = Field(default=None, max_length=64)
    active: bool | None = None

    @field_validator("code")
    @classmethod
    def normalize_code_opt(cls, v: str | None) -> str | None:
        return v.strip() if isinstance(v, str) else v


class SupplierOut(SupplierBase):
    id: int
    model_config = {"from_attributes": True}
