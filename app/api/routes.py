from fastapi import APIRouter
from app.routers import suppliers as suppliers_router
from app.routers import pricelists as pricelists_router
from app.routers import currencies as currencies_router  # NEW

api_router = APIRouter(prefix="/api")
api_router.include_router(suppliers_router.router)
api_router.include_router(pricelists_router.router)
api_router.include_router(currencies_router.router)  # NEW
