from fastapi import FastAPI

from app.api.routes import router as api_router
from app.core.config import settings
from app.models import category, manufacturer, price_list, supplier, supplier_product  # noqa: F401

app = FastAPI(title=settings.app_name)
app.include_router(api_router, prefix="/api")
