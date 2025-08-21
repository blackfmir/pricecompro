from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router
from app.core.config import settings
from app.web.views import router as ui_router

# ПОВЕРНУЛИ значення за замовчуванням (без '?v=...')
app = FastAPI(title=settings.app_name)


app.include_router(api_router, prefix="/api")
app.include_router(ui_router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Монтуємо static тільки якщо каталог існує
static_dir = Path(__file__).parent / "static"
if static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


