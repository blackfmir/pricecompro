# db_patch_add_start_urls.py
from sqlalchemy import create_engine, text
from app.core.config import settings  # якщо в config.py у тебе settings.DATABASE_URL
# або просто: DATABASE_URL = "sqlite:///pricecompro.db"

DATABASE_URL = getattr(settings, "DATABASE_URL", "sqlite:///pricecompro.db")

engine = create_engine(DATABASE_URL)

with engine.begin() as conn:
    # перевіряємо, чи є колонка
    cols = conn.exec_driver_sql("PRAGMA table_info(scrapers)").fetchall()
    have = any(c[1] == "start_urls_json" for c in cols)
    if not have:
        conn.exec_driver_sql("ALTER TABLE scrapers ADD COLUMN start_urls_json TEXT")
        # опціонально: заповнимо дефолтом "[]"
        conn.exec_driver_sql("UPDATE scrapers SET start_urls_json = '[]' WHERE start_urls_json IS NULL")
        print("Column start_urls_json added.")
    else:
        print("Column already exists.")
