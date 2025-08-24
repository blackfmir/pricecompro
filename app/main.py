from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.web.router import ui_router
from app.core.config import settings
from app.db.session import engine
from app.models.base import Base
from app import models  # noqa: F401  # імпорт щоб зареєструвати моделі


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME)

    # CORS (можеш вимкнути, якщо не треба)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Статичні файли та майбутнє сховище
    Path("app/static").mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    app.mount(settings.STORAGE_PUBLIC_BASE, StaticFiles(directory=settings.STORAGE_DIR), name="storage")


    # Роутери
    app.include_router(api_router)
    app.include_router(ui_router)

    # Ініціалізація БД (для швидкого старту без alembic)
    Base.metadata.create_all(bind=engine)
    return app


app = create_app()
