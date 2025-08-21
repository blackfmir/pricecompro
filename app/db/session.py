from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# для SQLite треба параметр check_same_thread=False у рядку підключення для sqlite+aiosqlite,
# але тут sync-движок, тож достатньо звичайного рядка
engine = create_engine(
    settings.database_url,
    future=True,
    echo=False,  # поставити True для SQL-логів
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
