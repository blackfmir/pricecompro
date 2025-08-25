from sqlalchemy import Integer, String, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class sync_profiles(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class sync_profile_rules(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    # цільове поле в products (включно з кастомними: code з custom_fields або ключ у extra_json)
    target_field: Mapped[str] = mapped_column(String(64), nullable=False)

    # з чого беремо (джерело у supplier_products):
    #   - стандартне: name, price_raw, manufacturer_raw, ...
    #   - extra:<key>  (для кастомних/додаткових)
    source: Mapped[str] = mapped_column(String(128), nullable=False)

    # режим оновлення
    # ignore | create_only | update_if_empty | always
    mode: Mapped[str] = mapped_column(String(32), default="always")

    # трансформація (необов’язково): шаблон або невеликий пайплайн
    # приклад: {"type":"template","value":"{width}×{height}×{length} мм"}
    # або {"type":"concat","fields":["ean","upc"],"sep":" | "}
    transform: Mapped[str | None] = mapped_column(JSON().with_variant(String, "sqlite"), nullable=True)
