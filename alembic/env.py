from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# додаємо шлях до app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.base import Base  # наш metadata
# Імпортуємо моделі для реєстрації таблиць у metadata (side-effect)
from app.models import supplier, price_list, supplier_product  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
