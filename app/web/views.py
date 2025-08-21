# app/web/views.py
from __future__ import annotations

from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import app.crud.brand_map as brand_map_crud
import app.crud.category_map as category_map_crud
import app.crud.supplier_product as sp_crud
from app.crud import price_list as price_list_crud
from app.crud import supplier as supplier_crud
from app.db.session import SessionLocal
from app.models.category import Category
from app.models.manufacturer import Manufacturer
from app.schemas.price_list import PriceListCreate
from app.schemas.supplier import SupplierCreate
from app.schemas.supplier_product import SupplierProductCreate
from app.services.importer import import_xlsx_bytes, import_xml_bytes

templates = Jinja2Templates(directory="app/web/templates")
router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DBSession = Annotated[Session, Depends(get_db)]
FileUpload = Annotated[UploadFile, File(...)]

# -------- Dashboard
@router.get("/")
def dashboard(request: Request, db: DBSession):
    total_sup = len(supplier_crud.list_(db))
    total_pl = len(price_list_crud.list_(db))
    total_sp = sp_crud.list_(db, limit=1, offset=0)["total"]
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "total_sup": total_sup, "total_pl": total_pl, "total_sp": total_sp},
    )


# -------- Suppliers
@router.get("/ui/suppliers")
def ui_suppliers(request: Request, db: DBSession):
    items = supplier_crud.list_(db)
    return templates.TemplateResponse("suppliers_list.html", {"request": request, "items": items})


@router.post("/ui/suppliers")
def ui_suppliers_create(
    request: Request,
    db: DBSession,
    name: str = Form(...),
    code: str = Form(...),
    active: bool = Form(True),
):
    supplier_crud.create(db, SupplierCreate(name=name, code=code, active=active))
    return RedirectResponse(url="/ui/suppliers", status_code=303)


# -------- Price lists
@router.get("/ui/price-lists")
def ui_price_lists(request: Request, db: DBSession):
    items = price_list_crud.list_(db)
    suppliers = supplier_crud.list_(db)
    return templates.TemplateResponse(
        "price_lists_list.html",
        {"request": request, "items": items, "suppliers": suppliers},
    )


@router.post("/ui/price-lists")
def ui_price_lists_create(
    request: Request,
    db: DBSession,
    supplier_id: int = Form(...),
    name: str = Form(...),
    format: str = Form("xml"),
):
    payload = PriceListCreate(
        supplier_id=supplier_id,
        name=name,
        source_type="local",
        source_config={"containers": {"items": "/list/product"}},
        format=format,
        mapping={
            "product_fields": {
                "supplier_sku": {
                    "by": "xpath",
                    "value": "./attributes/attribute[@eid='TRADE_INDEX']/value/text()",
                },
                "name": {"by": "xpath", "value": "./name/text()"},
                "description_raw": {"by": "xpath", "value": "./longDescription/text()"},
                "price_raw": {"by": "xpath", "value": "./price/text()"},
                "currency_raw": {"by": "xpath", "value": "./currency/text()"},
                "qty_raw": {"by": "xpath", "value": "./availabilityCount/text()"},
                "category_raw": {"by": "xpath", "value": "./category/text()"},
                "image_urls": {"by": "xpath_list", "value": "./allImages/imageUrl/text()"},
            }
        },
        active=True,
    )
    price_list_crud.create(db, payload)
    return RedirectResponse(url="/ui/price-lists", status_code=303)


# -------- Import form + upload
@router.get("/ui/price-lists/{pl_id}/import")
def ui_import_form(request: Request, db: DBSession, pl_id: int):
    pl = price_list_crud.get(db, pl_id)
    return templates.TemplateResponse("import_form.html", {"request": request, "pl": pl})


@router.post("/ui/price-lists/{pl_id}/import")
async def ui_import_upload(request: Request, db: DBSession, pl_id: int, file: FileUpload):
    pl = price_list_crud.get(db, pl_id)
    if not pl:
        raise HTTPException(status_code=404, detail="Price list not found")

    content = await file.read()
    fmt = (pl.format or "").lower()

    mapping_dict: dict[str, Any] = cast(dict[str, Any], pl.mapping or {})
    source_cfg: dict[str, Any] = cast(dict[str, Any], pl.source_config or {})

    items: list[SupplierProductCreate] = []
    errors: list[str] = []

    if fmt in {"xlsx", "xls"}:
        items, errors = import_xlsx_bytes(
            file_bytes=content,
            supplier_id=pl.supplier_id,
            price_list_id=pl.id,
            mapping=mapping_dict,
            source_config=source_cfg,
        )
    elif fmt in {"xml", "yml"}:
        items, errors = import_xml_bytes(
            file_bytes=content,
            supplier_id=pl.supplier_id,
            price_list_id=pl.id,
            mapping=mapping_dict,
            source_config=source_cfg,
        )
    else:
        errors = [f"Format {fmt} not supported in UI; use API."]

    stats = sp_crud.upsert_many(db, items)
    return templates.TemplateResponse(
        "import_form.html",
        {"request": request, "pl": pl, "stats": stats, "errors": errors, "preview": items[:5]},
    )


# -------- Supplier products (list)
@router.get("/ui/supplier-products")
def ui_supplier_products(
    request: Request,
    db: DBSession,
    supplier_id: int | None = None,
    q: str | None = None,
    page: int = 1,
    per_page: int = 50,
):
    offset = (page - 1) * per_page
    data = sp_crud.list_(db, supplier_id=supplier_id, q=q, limit=per_page, offset=offset)
    return templates.TemplateResponse(
        "supplier_products.html",
        {
            "request": request,
            "items": data["items"],
            "total": data["total"],
            "page": page,
            "per_page": per_page,
            "supplier_id": supplier_id,
            "q": q,
        },
    )


# -------- Normalization UI
@router.get("/ui/normalize")
def ui_normalize(request: Request, db: DBSession, supplier_id: int | None = None):
    suppliers = supplier_crud.list_(db)
    if not suppliers:
        return templates.TemplateResponse(
            "normalize.html",
            {"request": request, "suppliers": [], "supplier_id": None},
        )
    if supplier_id is None:
        supplier_id = suppliers[0].id

    brand_sugs = brand_map_crud.suggestions(db, supplier_id, 200)
    cat_sugs = category_map_crud.suggestions(db, supplier_id, 200)
    manufacturers = db.query(Manufacturer).order_by(Manufacturer.name).all()
    categories = db.query(Category).order_by(Category.name).all()

    return templates.TemplateResponse(
        "normalize.html",
        {
            "request": request,
            "suppliers": suppliers,
            "supplier_id": supplier_id,
            "brand_sugs": brand_sugs,
            "cat_sugs": cat_sugs,
            "manufacturers": manufacturers,
            "categories": categories,
        },
    )


@router.post("/ui/normalize/brand-map")
def ui_add_brand_map(
    request: Request,
    db: DBSession,
    supplier_id: int = Form(...),
    raw_name: str = Form(...),
    manufacturer_id: int = Form(...),
):
    brand_map_crud.create(db, supplier_id, raw_name, int(manufacturer_id))
    return RedirectResponse(url=f"/ui/normalize?supplier_id={supplier_id}", status_code=303)


@router.post("/ui/normalize/category-map")
def ui_add_category_map(
    request: Request,
    db: DBSession,
    supplier_id: int = Form(...),
    raw_name: str = Form(...),
    category_id: int = Form(...),
):
    category_map_crud.create(db, supplier_id, raw_name, int(category_id))
    return RedirectResponse(url=f"/ui/normalize?supplier_id={supplier_id}", status_code=303)


@router.post("/ui/normalize/apply")
def ui_apply_maps(request: Request, db: DBSession, supplier_id: int = Form(...)):
    # викликаємо, але не зберігаємо в змінні (щоб Ruff не лаявся на F841)
    brand_map_crud.apply_to_products(db, supplier_id)
    category_map_crud.apply_to_products(db, supplier_id)
    return RedirectResponse(url=f"/ui/normalize?supplier_id={supplier_id}", status_code=303)
