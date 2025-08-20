from fastapi import FastAPI
from app.core.config import settings
from app.api.routes import router as api_router
from app.db.session import engine
from app.models.base import Base
from app.models import supplier, price_list  # noqa: F401

app = FastAPI(title=settings.app_name)

# створюємо таблиці автоматично для старту (у продакшені - через Alembic)
Base.metadata.create_all(bind=engine)

app.include_router(api_router, prefix="/api")
