from fastapi import FastAPI

from app.api.routes import router as api_router
from app.core.config import settings

# ПОВЕРНУЛИ значення за замовчуванням (без '?v=...')
app = FastAPI(
    title=settings.app_name,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.include_router(api_router, prefix="/api")
print(">>> DB URL:", settings.database_url)


