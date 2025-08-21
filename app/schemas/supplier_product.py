from app.schemas.common import ORMModel


class SupplierProductBase(ORMModel):
    supplier_id: int
    price_list_id: int | None = None
    supplier_sku: str
    name: str | None = None
    manufacturer_sku: str | None = None
    mpn: str | None = None
    gtin: str | None = None
    ean: str | None = None
    upc: str | None = None
    jan: str | None = None
    isbn: str | None = None
    brand_raw: str | None = None
    category_raw: str | None = None
    price_raw: float | None = None
    currency_raw: str | None = None
    qty_raw: float | None = None
    availability_text: str | None = None
    delivery_terms: str | None = None
    delivery_date: str | None = None
    location: str | None = None
    short_description_raw: str | None = None
    description_raw: str | None = None
    image_urls: list[str] | None = None

class SupplierProductCreate(SupplierProductBase):
    pass

class SupplierProductUpdate(ORMModel):
    name: str | None = None
    price_raw: float | None = None
    currency_raw: str | None = None
    qty_raw: float | None = None
    availability_text: str | None = None
    short_description_raw: str | None = None
    description_raw: str | None = None
    image_urls: list[str] | None = None

class SupplierProductOut(SupplierProductBase):
    id: int
