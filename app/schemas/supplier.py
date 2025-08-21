from app.schemas.common import ORMModel


class SupplierBase(ORMModel):
    name: str
    code: str | None = None
    active: bool = True

class SupplierCreate(SupplierBase):
    pass

class SupplierUpdate(ORMModel):
    name: str | None = None
    code: str | None = None
    active: bool | None = None

class SupplierOut(SupplierBase):
    id: int
