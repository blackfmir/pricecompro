from typing import Literal
from pydantic import BaseModel, Field


SourceType = Literal["local", "http", "ftp", "parser"]
FormatType = Literal["xlsx", "csv", "xml", "json", "html"]


class PricelistBase(BaseModel):
    supplier_id: int
    name: str = Field(min_length=1, max_length=255)
    source_type: SourceType = "local"
    format: FormatType = "xlsx"
    source_config: str | None = None  # JSON у тексті
    mapping: str | None = None        # JSON у тексті
    active: bool = True


class PricelistCreate(PricelistBase):
    pass


class PricelistUpdate(BaseModel):
    supplier_id: int | None = None
    name: str | None = Field(default=None, max_length=255)
    source_type: SourceType | None = None
    format: FormatType | None = None
    source_config: str | None = None
    mapping: str | None = None
    active: bool | None = None


class PricelistOut(PricelistBase):
    id: int
    model_config = {"from_attributes": True}
