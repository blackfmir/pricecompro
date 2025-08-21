# app/core/config.py
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Python-імена (нижній регістр); .env -> alias у ВЕРХНЬОМУ регістрі
    database_url: str = Field(default="sqlite:///./pricecompro.db", alias="DATABASE_URL")
    app_env: str = Field(default="dev", alias="APP_ENV")
    app_name: str = Field(default="Price Complex Processor (PriceComPro)", alias="APP_NAME")
    storage_dir: str = Field(default="storage", alias="STORAGE_DIR")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,  # дозволяє використовувати python-імена
    )


settings = Settings()
