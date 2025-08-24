from fastapi import APIRouter, Depends, Request, Query
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.crud import supplier_product as sp_crud
from app.crud import supplier as supplier_crud
from app.crud import pricelists as pricelist_crud
import math

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

ALLOWED_LIMITS = (30, 50, 100)

@router.get("/ui/supplier-products")
def ui_supplier_products(
    request: Request,
    supplier_id: int | None = Query(default=None),
    pricelist_id: int | None = Query(default=None),
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=30),
    db: Session = Depends(get_db),
):
    if limit not in ALLOWED_LIMITS:
        limit = 30
    items, total = sp_crud.list_paged(
        db,
        supplier_id=supplier_id,
        pricelist_id=pricelist_id,
        q=q,
        page=page,
        page_size=limit,
    )
    pages_total = max(1, math.ceil(total / limit)) if total else 1

    # просте вікно сторінок (до 10 показів)
    page_numbers = list(range(1, min(pages_total, 10) + 1)) if pages_total <= 10 else []
    if not page_numbers and pages_total > 10:
        start = max(1, page - 2)
        end = min(pages_total, page + 2)
        page_numbers = [1]
        if start > 2:
            page_numbers.append(start - 1)  # «…» у шаблоні виведемо як disabled
        page_numbers.extend(range(start, end + 1))
        if end < pages_total - 1:
            page_numbers.append(end + 1)    # «…»
        page_numbers.append(pages_total)

    suppliers = {s.id: s.name for s in supplier_crud.list_(db)}
    pricelists = {p.id: p.name for p in pricelist_crud.list_(db)}
    return templates.TemplateResponse(
        "supplier_products.html",
        {
            "request": request,
            "items": items,
            "suppliers": suppliers,
            "pricelists": pricelists,
            "q": q or "",
            "supplier_id": supplier_id,
            "pricelist_id": pricelist_id,
            "limit": limit,
            "page": page,
            "total": total,
            "pages_total": pages_total,
            "page_numbers": page_numbers,
        },
    )
