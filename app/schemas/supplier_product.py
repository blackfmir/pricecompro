from pydantic import BaseModel, Field

class SupplierProductBase(BaseModel):
    supplier_id: int
    pricelist_id: int
    supplier_sku: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=512)

    price_raw: float | None = None
    currency_raw: str | None = None
    availability_raw: str | None = None

    manufacturer_raw: str | None = None
    manufacturer_id: int | None = None
    category_raw: str | None = None
    category_id: int | None = None

    is_active: bool = True

class SupplierProductCreate(SupplierProductBase):
    pass

class SupplierProductUpdate(BaseModel):
    # все опційно для патчів
    name: str | None = None
    price_raw: float | None = None
    currency_raw: str | None = None
    availability_raw: str | None = None
    manufacturer_raw: str | None = None
    manufacturer_id: int | None = None
    category_raw: str | None = None
    category_id: int | None = None
    is_active: bool | None = None

class SupplierProductOut(SupplierProductBase):
    id: int
    class Config:
        from_attributes = True
