from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Додаємо корінь проекту у sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Імпортуємо налаштування та моделі
from app.core.config import settings

# реєструємо всі моделі, щоб metadata «бачила» таблиці
from app.models import (  # noqa: F401
    category,
    currency,
    manufacturer,
    price_list,
    supplier,
    supplier_product,
)
from app.models.base import Base

# Це конфіг Alembic (з alembic.ini), але URL перезапишемо з settings
config = context.config

# Якщо в .env задано DATABASE_URL — використовуємо його і для Alembic
if getattr(settings, "DATABASE_URL", None):
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    print(f">>> ALEMBIC DB URL: {settings.DATABASE_URL}")

# Логування alembic (не обов’язково, але корисно)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# metadata для авто-генерації
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Запуск міграцій в офлайн-режимі (генерує SQL)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Запуск міграцій в онлайн-режимі (підключення до БД)."""
    # Базова секція alembic.ini
    section = config.get_section(config.config_ini_section) or {}
    # Гарантовано підставляємо URL з .env (settings.DATABASE_URL)
    from app.core.config import settings  # локальний імпорт, щоб не ламати імпорт-час
    section["sqlalchemy.url"] = settings.database_url

    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()



if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
