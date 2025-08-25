from pydantic import BaseModel, Field

class CustomFieldBase(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    code: str = Field(min_length=1, max_length=64)
    data_type: str = Field(pattern="^(text|number|date|bool)$")
    active: bool = True

class CustomFieldCreate(CustomFieldBase):
    pass

class CustomFieldUpdate(BaseModel):
    name: str | None = None
    data_type: str | None = None
    active: bool | None = None

class CustomFieldOut(CustomFieldBase):
    id: int
    class Config:
        from_attributes = True
