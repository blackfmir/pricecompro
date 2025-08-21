from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = Field(default="Price Complex Processor (PriceComPro)")
    app_env: str = Field(default="dev")
    database_url: str = Field(default="sqlite:///./pricecompro.db")

    model_config = {
        "env_prefix": "",           # читаємо змінні як є (DATABASE_URL, APP_ENV, ...)
        "env_file": ".env",
        "extra": "ignore",
    }

settings = Settings()
