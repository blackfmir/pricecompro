from fastapi import FastAPI
from app.core.config import settings
from app.api.routes import router as api_router
from app.models import supplier, price_list, supplier_product  # noqa: F401  # side-effect

app = FastAPI(title=settings.app_name)
app.include_router(api_router, prefix="/api")
