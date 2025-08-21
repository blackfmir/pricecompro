from sqlalchemy import engine_from_config, pool

from alembic import context
from app.core.config import settings
from app.models import category, manufacturer, price_list, supplier, supplier_product  # noqa: F401
from app.models.base import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)
target_metadata = Base.metadata
