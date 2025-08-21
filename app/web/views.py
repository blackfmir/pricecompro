# app/web/views.py
from __future__ import annotations

from typing import Annotated, Any, TypeAlias, cast

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
from app.schemas.price_list import PriceListCreate, PriceListUpdate
from app.schemas.supplier import SupplierCreate
from app.schemas.supplier_product import SupplierProductCreate
from app.services.importer import import_xlsx_bytes, import_xml_bytes
from app.utils.storage import save_price_upload

templates = Jinja2Templates(directory="app/web/templates")
router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DBSession = Annotated[Session, Depends(get_db)]
UploadFileForm: TypeAlias = Annotated[UploadFile, File(...)]


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

@router.get("/ui/suppliers/{supplier_id}/edit")
def ui_supplier_edit(request: Request, db: DBSession, supplier_id: int):
    s = db.get(supplier_crud.Supplier, supplier_id) if hasattr(supplier_crud, "Supplier") else None  # guard
    if not s:
        from app.models.supplier import Supplier as SupplierModel
        s = db.get(SupplierModel, supplier_id)
    if not s:
        raise HTTPException(404, "Supplier not found")
    return templates.TemplateResponse("supplier_edit.html", {"request": request, "s": s})

@router.post("/ui/suppliers/{supplier_id}/edit")
def ui_supplier_update(
    request: Request,
    db: DBSession,
    supplier_id: int,
    name: str = Form(...),
    active: bool = Form(False),
):
    from app.schemas.supplier import SupplierUpdate
    supplier_crud.update(db, supplier_id, SupplierUpdate(name=name, code=None, active=active))
    return RedirectResponse(url="/ui/suppliers?msg=updated", status_code=303)


@router.post("/ui/suppliers/{supplier_id}/delete")
def ui_supplier_delete(request: Request, db: DBSession, supplier_id: int):
    ok, reason = supplier_crud.delete(db, supplier_id)
    if not ok:
        msg = "Supplier not found" if reason == "not_found" else "Cannot delete: supplier has price lists"
        return RedirectResponse(url=f"/ui/suppliers?err={msg}", status_code=303)
    return RedirectResponse(url="/ui/suppliers?msg=deleted", status_code=303)



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

@router.get("/ui/price-lists/{pl_id}/edit")
def ui_price_list_edit(request: Request, db: DBSession, pl_id: int):
    pl = price_list_crud.get(db, pl_id)
    if not pl:
        raise HTTPException(404, "Price list not found")

    src: dict[str, Any] = cast(dict[str, Any], pl.source_config or {})
    fmt = (pl.format or "xml").lower()
    s_type = (pl.source_type or "local").lower()

    # Загальні витяги з source_config
    local_path = src.get("local_path", "")
    url_link = src.get("url", "")
    downloaded_path = src.get("downloaded_path", "")
    ftp_cfg = src.get("ftp", {}) or {}
    local_url = src.get("local_url", "")
    downloaded_path = src.get("downloaded_path", "")
    downloaded_url = src.get("downloaded_url", "")

    # Налаштування під формат
    sheet = src.get("sheet", {}) or {}
    xlsx_sheet_by = sheet.get("by", "name")        # name | index
    xlsx_sheet_value = sheet.get("value", "")

    csv_delimiter = src.get("delimiter", ";")
    csv_encoding = src.get("encoding", "utf-8")

    containers = src.get("containers", {}) or {}
    xml_items_container = containers.get("items", "")
    xml_use_xpath = containers.get("use_xpath", True)

    # Мапінг (підтримуємо базові поля)
    mapping: dict[str, Any] = cast(dict[str, Any], pl.mapping or {})
    pf: dict[str, Any] = mapping.get("product_fields", {}) or {}

    def get_field_spec(key: str) -> tuple[str, str]:
        """Повертає (mode, value) для відображення в UI, залежно від формату."""
        spec = pf.get(key) or {}
        by = spec.get("by")
        value = str(spec.get("value", "") or "")
        if fmt in {"xlsx", "xls"}:
            # дозволяємо col_letter | col_index
            if by in {"col_letter", "col_index"}:
                return by, value
            return "col_letter", ""
        if fmt == "csv":
            # CSV завжди col_index
            return "col_index", value
        # xml/yml
        if by in {"xpath", "xpath_list"}:
            return ("xpath", value)
        # якщо колись збережено як tag — покажемо як tag
        if by == "tag":
            return ("tag", value)
        return "xpath", ""

    # Підготуємо початкові значення для полів мапінгу:
    map_keys = ["supplier_sku", "name", "price_raw", "currency_raw", "qty_raw", "category_raw", "image_urls"]
    mapping_ui: dict[str, dict[str, str]] = {}
    for k in map_keys:
        mode, value = get_field_spec(k)
        mapping_ui[k] = {"mode": mode, "value": value}

    # split для image_urls (CSV/XLSX)
    img_spec = pf.get("image_urls") or {}
    img_opts = img_spec.get("options", {}) or {}
    image_urls_split = img_opts.get("split", "")

    return templates.TemplateResponse(
        "price_list_edit.html",
        {
            "request": request,
            "pl": pl,
            "source_type": s_type,
            "format": fmt,
            "local_path": local_path,
            "url_link": url_link,
            "local_url": local_url,
            "downloaded_path": downloaded_path,
            "downloaded_url": downloaded_url,
            "ftp_cfg": ftp_cfg,
            "xlsx_sheet_by": xlsx_sheet_by,
            "xlsx_sheet_value": xlsx_sheet_value,
            "csv_delimiter": csv_delimiter,
            "csv_encoding": csv_encoding,
            "xml_items_container": xml_items_container,
            "xml_use_xpath": xml_use_xpath,
            "mapping_ui": mapping_ui,
            "image_urls_split": image_urls_split,
        },
    )


@router.post("/ui/price-lists/{pl_id}/edit")
async def ui_price_list_update(request: Request, db: DBSession, pl_id: int):
    pl = price_list_crud.get(db, pl_id)
    if not pl:
        raise HTTPException(404, "Price list not found")

    form = await request.form()
    name = str(form.get("name") or pl.name)
    fmt = (str(form.get("format") or pl.format or "xml")).lower()
    s_type = (str(form.get("source_type") or pl.source_type or "local")).lower()

    # source_config, який будемо оновлювати
    src: dict[str, Any] = cast(dict[str, Any], pl.source_config or {})
    src = dict(src)  # копія

    # -- секція Source type
    if s_type == "local":
        # показуємо лише шлях; аплоад робиться окремим ендпоїнтом
        # якщо потрібно зберегти вручну змінений шлях:
        local_path = str(form.get("local_path") or src.get("local_path") or "")
        if local_path:
            src["local_path"] = local_path

    elif s_type == "http":
        url_link = str(form.get("link") or "")
        if url_link:
            src["url"] = url_link
        # downloaded_path показуємо як read-only (можна не чіпати)

    elif s_type == "ftp":
        ftp_host = str(form.get("ftp_host") or "")
        ftp_port_raw = form.get("ftp_port")
        try:
            ftp_port = int(str(ftp_port_raw))
        except (TypeError, ValueError):
            ftp_port = 21
        ftp_user = str(form.get("ftp_user") or "")
        ftp_pass = str(form.get("ftp_pass") or "")
        ftp_remote = str(form.get("ftp_remote") or "")
        src["ftp"] = {
            "host": ftp_host,
            "port": ftp_port,
            "user": ftp_user,
            "password": ftp_pass,
            "remote_path": ftp_remote,
        }

    elif s_type == "parser":
        # просто placeholder
        src["parser"] = {"note": "planned"}

    # -- секція Format
    if fmt in {"xlsx", "xls"}:
        xlsx_sheet_by = str(form.get("xlsx_sheet_by") or "name")  # name|index
        xlsx_sheet_value = str(form.get("xlsx_sheet_value") or "")
        src["sheet"] = {"by": xlsx_sheet_by, "value": xlsx_sheet_value}

    elif fmt == "csv":
        csv_delimiter = str(form.get("csv_delimiter") or ";")
        csv_encoding = str(form.get("csv_encoding") or "utf-8")
        src["delimiter"] = csv_delimiter
        src["encoding"] = csv_encoding

    elif fmt in {"xml", "yml"}:
        xml_items_container = str(form.get("xml_items_container") or "")
        xml_use_xpath = (form.get("xml_use_xpath") == "on")
        src["containers"] = {"items": xml_items_container, "use_xpath": xml_use_xpath}

    # -- секція Mapping (мінімальний набір полів)
    def build_spec_text(value: str, mode: str) -> dict[str, Any] | None:
        if not value:
            return None
        if fmt in {"xlsx", "xls"}:
            if mode == "col_index":
                try:
                    idx = int(value)
                except Exception:
                    return None
                return {"by": "col_index", "value": idx}
            return {"by": "col_letter", "value": value}
        if fmt == "csv":
            try:
                idx = int(value)
            except Exception:
                return None
            return {"by": "col_index", "value": idx}
        # xml/yml
        if mode == "tag":
            # перетворюємо просту назву на xpath до текстового вузла
            return {"by": "xpath", "value": f"./{value}/text()"}
        return {"by": "xpath", "value": value}

    def build_spec_list(value: str, mode: str, split: str) -> dict[str, Any] | None:
        if not value:
            return None
        spec = build_spec_text(value, mode)
        if not spec:
            return None
        if fmt in {"xlsx", "xls", "csv"}:
            # для табличних форматів можна розділяти список строкою
            if split:
                spec["options"] = {"split": split}
            return spec
        # xml/yml: очікуємо xpath_list, якщо явний xpath
        by = spec.get("by")
        if by == "xpath":
            spec["by"] = "xpath_list"
        return spec

    map_fields = {
        "supplier_sku": "map_supplier_sku_",
        "name": "map_name_",
        "price_raw": "map_price_raw_",
        "currency_raw": "map_currency_raw_",
        "qty_raw": "map_qty_raw_",
        "category_raw": "map_category_raw_",
        "image_urls": "map_image_urls_",
    }

    product_fields: dict[str, Any] = {}
    for key, prefix in map_fields.items():
        mode = str(form.get(prefix + "mode") or "")
        value = str(form.get(prefix + "value") or "")
        if key == "image_urls":
            split = str(form.get(prefix + "split") or "")
            spec = build_spec_list(value, mode, split)
        else:
            spec = build_spec_text(value, mode)
        if spec:
            product_fields[key] = spec

    new_mapping = {"product_fields": product_fields} if product_fields else (pl.mapping or {})

    payload = PriceListUpdate(
        name=name,
        format=fmt,
        source_type=s_type,
        source_config=src,
        mapping=new_mapping,
        active=pl.active,
    )
    obj = price_list_crud.update(db, pl_id, payload)
    if not obj:
        raise HTTPException(404, "Price list not found")
    return RedirectResponse(url="/ui/price-lists?msg=updated", status_code=303)


@router.post("/ui/price-lists/{pl_id}/delete")
def ui_price_list_delete(request: Request, db: DBSession, pl_id: int):
    ok = price_list_crud.delete(db, pl_id)
    if not ok:
        return RedirectResponse(url="/ui/price-lists?err=not_found", status_code=303)
    return RedirectResponse(url="/ui/price-lists?msg=deleted", status_code=303)

@router.post("/ui/price-lists/{pl_id}/upload-source")
async def ui_upload_source(request: Request, db: DBSession, pl_id: int, file: UploadFileForm):
    pl = price_list_crud.get(db, pl_id)
    if not pl:
        raise HTTPException(404, "Price list not found")

    content = await file.read()
    path, url = save_price_upload(pl_id, file.filename or "source.bin", content)

    src: dict[str, Any] = cast(dict[str, Any], pl.source_config or {})
    src = dict(src)
    # фіксуємо і файловий шлях, і URL для відображення/завантаження
    src["local_path"] = str(path)
    src["local_url"] = url

    payload = PriceListUpdate(
        name=pl.name,
        format=pl.format or "xml",
        source_type="local",
        source_config=src,
        mapping=pl.mapping,
        active=pl.active,
    )
    price_list_crud.update(db, pl_id, payload)
    return RedirectResponse(url=f"/ui/price-lists/{pl_id}/edit?msg=uploaded", status_code=303)


# -------- Import form + upload
@router.get("/ui/price-lists/{pl_id}/import")
def ui_import_form(request: Request, db: DBSession, pl_id: int):
    pl = price_list_crud.get(db, pl_id)
    return templates.TemplateResponse("import_form.html", {"request": request, "pl": pl})


@router.post("/ui/price-lists/{pl_id}/import")
async def ui_import_upload(request: Request, db: DBSession, pl_id: int, file: UploadFileForm):

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
    brand_maps = brand_map_crud.list_(db, supplier_id)
    category_maps = category_map_crud.list_(db, supplier_id)

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
            "brand_maps": brand_maps,
            "category_maps": category_maps,
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

@router.post("/ui/normalize/brand-map/{bm_id}/edit")
def ui_edit_brand_map(request: Request, db: DBSession, bm_id: int, supplier_id: int = Form(...), manufacturer_id: int = Form(...)):
    brand_map_crud.update(db, bm_id, int(manufacturer_id))
    return RedirectResponse(url=f"/ui/normalize?supplier_id={supplier_id}", status_code=303)

@router.post("/ui/normalize/brand-map/{bm_id}/delete")
def ui_delete_brand_map(request: Request, db: DBSession, bm_id: int, supplier_id: int = Form(...)):
    brand_map_crud.delete(db, bm_id)
    return RedirectResponse(url=f"/ui/normalize?supplier_id={supplier_id}", status_code=303)

@router.post("/ui/normalize/category-map/{cm_id}/edit")
def ui_edit_category_map(request: Request, db: DBSession, cm_id: int, supplier_id: int = Form(...), category_id: int = Form(...)):
    category_map_crud.update(db, cm_id, int(category_id))
    return RedirectResponse(url=f"/ui/normalize?supplier_id={supplier_id}", status_code=303)

@router.post("/ui/normalize/category-map/{cm_id}/delete")
def ui_delete_category_map(request: Request, db: DBSession, cm_id: int, supplier_id: int = Form(...)):
    category_map_crud.delete(db, cm_id)
    return RedirectResponse(url=f"/ui/normalize?supplier_id={supplier_id}", status_code=303)

