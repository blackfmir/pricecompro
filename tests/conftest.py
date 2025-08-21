# tests/conftest.py
import os
import pathlib

# 1) окремий URL для тестів (до імпорту app.*)
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

from app.db.session import engine  # noqa: E402
from app.models.base import Base  # noqa: E402


def pytest_sessionstart(session):
    # 2) перед тестами гарантуємо чисту БД
    p = pathlib.Path("test.db")
    if p.exists():
        p.unlink()
    Base.metadata.create_all(bind=engine)
