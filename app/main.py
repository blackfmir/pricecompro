# app/main.py
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.staticfiles import StaticFiles

from app.api.routes import router as api_router
from app.core.config import settings

# DEV: імпорт БД і моделей до create_all
from app.db.session import engine
from app.models import (  # noqa: F401
    # якщо додав моделі мапінгів:
    brand_map,
    category,
    category_map,
    manufacturer,
    price_list,
    supplier,
    supplier_product,
)
from app.models.base import Base
from app.web.views import router as ui_router

app = FastAPI(title=settings.app_name)

# DEV: автостворення таблиць (прибери в проді)
Base.metadata.create_all(bind=engine)

# API + UI
app.include_router(api_router, prefix="/api")
app.include_router(ui_router)

# Статика тільки якщо каталог існує
static_dir = Path(__file__).parent / "static"
if static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    app.mount("/storage", StaticFiles(directory=settings.STORAGE_DIR), name="storage")

