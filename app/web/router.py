from fastapi import APIRouter
from app.views import suppliers as suppliers_views
from app.views import pricelists as pricelists_views
from app.views import currencies as currencies_views
from app.views import supplier_products as supplier_products_views
from app.views import fields as fields_views
from app.views import import_batches as import_batches_views  # NEW
from app.views import scrapers as scrapers_views  # NEW


ui_router = APIRouter()
ui_router.include_router(suppliers_views.router)
ui_router.include_router(pricelists_views.router)
ui_router.include_router(currencies_views.router)
ui_router.include_router(supplier_products_views.router)
ui_router.include_router(fields_views.router)
ui_router.include_router(import_batches_views.router)         # NEW
ui_router.include_router(scrapers_views.router)   # NEW



