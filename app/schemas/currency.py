from pydantic import BaseModel, ConfigDict, Field


class CurrencyBase(BaseModel):
    name: str
    iso_code: str = Field(min_length=3, max_length=3)
    symbol_left: str | None = None
    symbol_right: str | None = None
    decimals: int = 2
    rate: float = 1.0
    active: bool = True

class CurrencyCreate(CurrencyBase):
    pass

class CurrencyUpdate(BaseModel):
    name: str | None = None
    iso_code: str | None = None
    symbol_left: str | None = None
    symbol_right: str | None = None
    decimals: int | None = None
    rate: float | None = None
    active: bool | None = None

class CurrencyOut(CurrencyBase):
    id: int
    is_primary: bool
    model_config = ConfigDict(from_attributes=True)
