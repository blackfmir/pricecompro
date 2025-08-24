from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class CurrencyBase(BaseModel):
    code: str = Field(min_length=3, max_length=8)           # ISO-код або внутрішній
    name: str = Field(min_length=2, max_length=64)          # назва валюти
    rate_to_base: float = Field(gt=0)
    manual_override: bool = False
    active: bool = True

    symbol_left: str = Field(default="", max_length=8)
    symbol_right: str = Field(default="", max_length=8)
    decimals: int = Field(default=2, ge=0, le=8)

    @field_validator("code")
    @classmethod
    def upper_code(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("name", "symbol_left", "symbol_right")
    @classmethod
    def strip_fields(cls, v: str) -> str:
        return v.strip()


class CurrencyCreate(CurrencyBase):
    pass


class CurrencyUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=3, max_length=8)
    name: str | None = Field(default=None, min_length=2, max_length=64)
    rate_to_base: float | None = Field(default=None, gt=0)
    manual_override: bool | None = None
    active: bool | None = None

    symbol_left: str | None = Field(default=None, max_length=8)
    symbol_right: str | None = Field(default=None, max_length=8)
    decimals: int | None = Field(default=None, ge=0, le=8)

    @field_validator("code")
    @classmethod
    def upper_code_opt(cls, v: str | None) -> str | None:
        return v.strip().upper() if isinstance(v, str) else v

    @field_validator("name", "symbol_left", "symbol_right")
    @classmethod
    def strip_fields_opt(cls, v: str | None) -> str | None:
        return v.strip() if isinstance(v, str) else v


class CurrencyOut(CurrencyBase):
    id: int
    is_base: bool = False
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
