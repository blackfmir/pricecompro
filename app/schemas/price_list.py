from typing import Any

from app.schemas.common import ORMModel


class PriceListBase(ORMModel):
    supplier_id: int
    name: str
    source_type: str = "local"
    source_config: dict[str, Any] | None = None
    format: str | None = "csv"
    default_currency_id: int | None = None
    mapping: dict[str, Any] | None = None
    schedule: str | None = None
    active: bool = True

class PriceListCreate(PriceListBase):
    pass

class PriceListUpdate(ORMModel):
    name: str | None = None
    source_type: str | None = None
    source_config: dict[str, Any] | None = None
    format: str | None = None
    default_currency_id: int | None = None
    mapping: dict[str, Any] | None = None
    schedule: str | None = None
    active: bool | None = None

class PriceListOut(PriceListBase):
    id: int
    last_run_at: str | None = None
    last_status: str | None = None
    default_currency_id: int | None = None
