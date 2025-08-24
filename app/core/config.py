from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "PriceComPro"
    # Для старту — sqlite у корені. Перейдемо на Postgres пізніше.
    DATABASE_URL: str = "sqlite:///pricecompro.db"

    # Локальне файлове сховище (наступні етапи його використають)
    STORAGE_DIR: str = str((Path(__file__).resolve().parents[2] / "storage").absolute())
    STORAGE_PUBLIC_BASE: str = "/storage"

    class Config:
        env_file = ".env"


settings = Settings()

# Гарантуємо існування storage/
Path(settings.STORAGE_DIR).mkdir(parents=True, exist_ok=True)
