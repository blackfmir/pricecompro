from fastapi import APIRouter
from app.views import suppliers as suppliers_views
from app.views import pricelists as pricelists_views
from app.views import currencies as currencies_views  # NEW
from app.views import supplier_products as supplier_products_views  # NEW


ui_router = APIRouter()
ui_router.include_router(suppliers_views.router)
ui_router.include_router(pricelists_views.router)
ui_router.include_router(currencies_views.router)  # NEW
ui_router.include_router(supplier_products_views.router)  # NEW

