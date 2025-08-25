import json
from urllib.parse import quote
from pathlib import Path
from datetime import datetime
from io import StringIO   # ← ДОДАТИ
import csv 
from typing import List

from fastapi import APIRouter, Depends, Request, Form, UploadFile, File

from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.crud import pricelists as crud
from app.crud import supplier as supplier_crud
from app.crud import supplier_product as sp_crud
from app.crud import custom_field as cf_crud

from app.schemas.pricelists import PricelistCreate, PricelistUpdate

from app.utils.storage import save_upload, storage_join, public_url, to_rel
from app.services.importer import preview_from_file, to_supplier_products


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/ui/pricelists")
def ui_pricelists(request: Request, db: Session = Depends(get_db)):
    items = crud.list_(db)
    suppliers = {s.id: s.name for s in supplier_crud.list_(db)}
    # NEW: дані для модалки імпорту
    qp = request.query_params
    import_stats = None
    if qp.get("import") == "1":
        try:
            import_stats = {
                "inserted": int(qp.get("ins", "0")),
                "updated": int(qp.get("upd", "0")),
                "warnings": int(qp.get("warn", "0")),
            }
        except ValueError:
            import_stats = None
    return templates.TemplateResponse(
        "pricelists.html",
        {"request": request, "items": items, "suppliers": suppliers, "import_stats": import_stats},
    )


@router.get("/ui/pricelists/new")
def ui_pricelist_new(request: Request, db: Session = Depends(get_db)):
    suppliers = supplier_crud.list_(db)
    return templates.TemplateResponse(
        "pricelist_form.html",
        {"request": request, "item": None, "suppliers": suppliers},
    )


@router.post("/ui/pricelists/new")
def ui_pricelist_create(
    supplier_id: int = Form(...),
    name: str = Form(...),
    source_type: str = Form("local"),
    format: str = Form("xlsx"),
    source_config: str | None = Form(None),
    mapping: str | None = Form(None),
    active: bool = Form(False),  # важливо: False, щоб знятий чекбокс не ставав True
    db: Session = Depends(get_db),
):
    crud.create(
        db,
        PricelistCreate(
            supplier_id=supplier_id,
            name=name,
            source_type=source_type,  # type: ignore[arg-type]
            format=format,            # type: ignore[arg-type]
            source_config=source_config,
            mapping=mapping,
            active=active,
        ),
    )
    return RedirectResponse(url="/ui/pricelists", status_code=303)


@router.get("/ui/pricelists/{pr_id}/edit")
def ui_pricelist_edit(pr_id: int, request: Request, db: Session = Depends(get_db)):
    item = crud.get(db, pr_id)
    if not item:
        return RedirectResponse(url="/ui/pricelists", status_code=303)
    suppliers = supplier_crud.list_(db)

    # --- НОВЕ: інформація про останній файл ---
    file_info = None
    try:
        src_cfg = json.loads(item.source_config) if item.source_config else {}
        last_path: str | None = src_cfg.get("last_path")
        last_url: str | None = src_cfg.get("last_url")

        if last_path:
            abs_path = storage_join(last_path)
            p = Path(abs_path)
            if p.exists() and p.is_file():
                stat = p.stat()
                size: float = float(stat.st_size)   # ← було int, через /= ставало float і mypy сварився
                for unit in ["B", "KB", "MB", "GB"]:
                    if size < 1024.0:
                        size_h = f"{size:.1f} {unit}"
                        break
                    size /= 1024.0
                else:
                    size_h = f"{size:.1f} TB"

                file_info = {
                    "file_name": p.name,
                    "file_url": last_url or public_url(last_path),
                    "dir_rel": to_rel(p.parent),
                    "path_rel": last_path,
                    "size_bytes": stat.st_size,
                    "size_h": size_h,
                    "created_at": datetime.fromtimestamp(getattr(stat, "st_ctime", stat.st_mtime)).strftime("%Y-%m-%d %H:%M"),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                }
    except Exception:
        file_info = None
    # --- /НОВЕ ---

    return templates.TemplateResponse(
        "pricelist_form.html",
        {
            "request": request,
            "item": item,
            "suppliers": suppliers,
            "file_info": file_info,  # ← передаємо в шаблон
        },
    )


@router.post("/ui/pricelists/{pr_id}/edit")
def ui_pricelist_update(
    pr_id: int,
    supplier_id: int = Form(...),
    name: str = Form(...),
    source_type: str = Form("local"),
    format: str = Form("xlsx"),
    source_config: str | None = Form(None),
    mapping: str | None = Form(None),
    active: bool = Form(False),
    db: Session = Depends(get_db),
):
    crud.update(
        db,
        pr_id,
        PricelistUpdate(
            supplier_id=supplier_id,
            name=name,
            source_type=source_type,  # type: ignore[arg-type]
            format=format,            # type: ignore[arg-type]
            source_config=source_config,
            mapping=mapping,
            active=active,
        ),
    )
    return RedirectResponse(url="/ui/pricelists", status_code=303)


@router.post("/ui/pricelists/{pr_id}/delete")
def ui_pricelist_delete(pr_id: int, db: Session = Depends(get_db)):
    crud.delete(db, pr_id)
    return RedirectResponse(url="/ui/pricelists", status_code=303)


@router.post("/ui/pricelists/{pr_id}/import")
def ui_pricelist_import(pr_id: int, db: Session = Depends(get_db)):
    item = crud.get(db, pr_id)
    if not item:
        return RedirectResponse(url="/ui/pricelists?msg=" + quote("Прайс-лист не знайдено"), status_code=303)

    # 1) читаємо файл
    src_cfg = {}
    if item.source_config:
        try:
            src_cfg = json.loads(item.source_config)
        except Exception:
            src_cfg = {}
    last_path = src_cfg.get("last_path")
    if not last_path:
        return RedirectResponse(url="/ui/pricelists?msg=" + quote("Спочатку завантажте файл"), status_code=303)
    fp = storage_join(last_path)
    p = Path(fp)
    if not p.exists():
        return RedirectResponse(url="/ui/pricelists?msg=" + quote("Файл не знайдено у сховищі"), status_code=303)
    data = p.read_bytes()

    # 2) готуємо mapping/options
    try:
        mapping = json.loads(item.mapping) if item.mapping else {"fields": {}, "options": {}}
    except Exception:
        mapping = {"fields": {}, "options": {}}
    options = mapping.get("options", {})

    # 3) парсимо всі рядки (ліміт великий)
    rows, errors = preview_from_file(data=data, fmt=item.format, mapping=mapping, source_config=options, limit=200000)

    # 4) уніфікуємо в структуру supplier_products
    items = to_supplier_products(rows)

    # 5) upsert у БД
    stats = sp_crud.upsert_many(db, supplier_id=item.supplier_id, pricelist_id=item.id, items=items)
    msg = f"Імпорт: inserted={stats['inserted']}, updated={stats['updated']}"
    if errors:
        msg += f", warnings={len(errors)}"

    return RedirectResponse(
        url=f"/ui/pricelists?import=1&ins={stats['inserted']}&upd={stats['updated']}&warn={len(errors)}",
        status_code=303,
    )

@router.post("/ui/pricelists/{pr_id}/import-ajax")
def ui_pricelist_import_ajax(pr_id: int, db: Session = Depends(get_db)):
    item = crud.get(db, pr_id)
    if not item:
        return JSONResponse({"ok": False, "message": "Прайс-лист не знайдено"}, status_code=404)

    # 1) зчитуємо останній файл
    try:
        src_cfg = json.loads(item.source_config) if item.source_config else {}
    except Exception:
        src_cfg = {}
    last_path = src_cfg.get("last_path")
    if not last_path:
        return JSONResponse({"ok": False, "message": "Спочатку завантажте файл"}, status_code=400)

    fp = storage_join(last_path)
    p = Path(fp)
    if not p.exists():
        return JSONResponse({"ok": False, "message": "Файл не знайдено у сховищі"}, status_code=400)

    data = p.read_bytes()

    # 2) мапінг + опції
    try:
        mapping = json.loads(item.mapping) if item.mapping else {"fields": {}, "options": {}}
    except Exception:
        mapping = {"fields": {}, "options": {}}
    options = mapping.get("options", {})

    # 3) парсимо всі рядки
    rows, errors = preview_from_file(data=data, fmt=item.format, mapping=mapping, source_config=options, limit=200000)
    items_norm = to_supplier_products(rows)

    # 4) валідація обов'язкових полів
    from app.services.importer import split_valid_invalid  # локальний імпорт, щоб уникнути циклів
    valid_items, invalid_rows = split_valid_invalid(items_norm)

    # 5) upsert у БД лише валідних
    stats = sp_crud.upsert_many(
        db,
        supplier_id=item.supplier_id,
        pricelist_id=item.id,
        items=valid_items,                                          # ← ВАЖЛИВО
    )

    # 6) якщо є невалідні — формуємо CSV і кладемо у сховище
    errors_url = None
    if invalid_rows:
        buf = StringIO()
        fieldnames = ["__reason","supplier_sku","name","price","price_raw","currency_raw","availability_raw","manufacturer_raw","category_raw"]
        writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in invalid_rows:
            # додамо оригінальне price (якщо було)
            if "price" not in r and "price_raw" in r:
                r["price"] = r.get("price_raw")
            writer.writerow(r)
        csv_bytes = buf.getvalue().encode("utf-8-sig")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        rel, url = save_upload(f"pricelists/{item.id}/logs", f"errors_{item.id}_{ts}.csv", csv_bytes)
        errors_url = url

    return JSONResponse({
        "ok": True,
        "inserted": stats.get("inserted", 0),
        "updated": stats.get("updated", 0),
        "warnings": len(errors),
        "skipped": len(invalid_rows),
        "errors_url": errors_url,
        "message": f"Імпорт виконано для прайс-листа #{item.id}",
        "pricelist_id": item.id,
    })


@router.get("/ui/pricelists/{pr_id}/upload")
def ui_pricelist_upload_form(pr_id: int, request: Request, db: Session = Depends(get_db)):
    item = crud.get(db, pr_id)
    if not item:
        return RedirectResponse(url="/ui/pricelists", status_code=303)
    toast_message = request.query_params.get("msg")
    # Покажемо останній шлях із source_config (якщо є)
    src_cfg = {}
    if item.source_config:
        try:
            src_cfg = json.loads(item.source_config)
        except Exception:
            src_cfg = {}
    last_path = src_cfg.get("last_path")
    last_url = src_cfg.get("last_url")
    return templates.TemplateResponse(
        "pricelist_upload.html",
        {"request": request, "item": item, "last_path": last_path, "last_url": last_url, "toast_message": toast_message},
    )

@router.post("/ui/pricelists/{pr_id}/upload")
async def ui_pricelist_upload(pr_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    item = crud.get(db, pr_id)
    if not item:
        return RedirectResponse(url="/ui/pricelists?msg=" + quote("Прайс-лист не знайдено"), status_code=303)

    data = await file.read()
    fname = file.filename or "upload.bin"   # ← гарантуємо str
    rel, url = save_upload(f"pricelists/{pr_id}", fname, data)

    # збережемо в source_config останній шлях та URL
    src_cfg = {}
    if item.source_config:
        try:
            src_cfg = json.loads(item.source_config)
        except Exception:
            src_cfg = {}
    src_cfg["last_path"] = rel
    src_cfg["last_url"] = url
    item.source_config = json.dumps(src_cfg, ensure_ascii=False)

    db.commit()
    db.refresh(item)

    return RedirectResponse(
        url=f"/ui/pricelists/{pr_id}/upload?msg=" + quote(f"Файл збережено: {rel}"),
        status_code=303,
    )

@router.get("/ui/pricelists/{pr_id}/map")
def ui_pricelist_map(pr_id: int, request: Request, db: Session = Depends(get_db)):
    item = crud.get(db, pr_id)
    if not item:
        return RedirectResponse(url="/ui/pricelists", status_code=303)

    preview_rows: list[dict[str, str]] = []
    preview_errors: list[str] = []

    src_cfg = {}
    if item.source_config:
        try:
            src_cfg = json.loads(item.source_config)
        except Exception:
            src_cfg = {}
    last_path = src_cfg.get("last_path")
    file_meta = None
    file_bytes: bytes | None = None
    if last_path:
        fp = storage_join(last_path)
        p = Path(fp)
        if p.exists():
            file_bytes = p.read_bytes()
            file_meta = {
                "name": p.name,
                "url": src_cfg.get("last_url") or public_url(last_path),
                "path_rel": last_path,
            }

    # підготуємо дефолтний mapping для форм
    default_map = {
        "fields": {
            "supplier_sku": {"type": "literal", "value": ""},
            "name": {"type": "literal", "value": ""},
            "price": {"type": "literal", "value": ""},
            "availability": {"type": "literal", "value": ""},
            "manufacturer": {"type": "literal", "value": ""},
            "category": {"type": "literal", "value": ""},
            "currency": {"type": "literal", "value": ""},
        },
        "options": {},  # пер-форматні опції тут
    }
    try:
        mapping = json.loads(item.mapping) if item.mapping else default_map
    except Exception:
        mapping = default_map

    # якщо є файл — згенеруємо прев'ю
    preview_rows, preview_errors = [], []
    if file_bytes:
        # зберігаємо опції формату у mapping["options"]; для CSV/XLSX/XML UI їх вкаже
        fmt = (item.format or "").lower()
        options = mapping.get("options", {})
        preview_rows, preview_errors = preview_from_file(
            data=file_bytes, fmt=fmt, mapping=mapping, source_config=options, limit=20
        )

    custom_fields = cf_crud.list_(db, active_only=True)

    standard_fields = [
        ("description", "Опис"),
        ("images", "Зображення (URL/CSV)"),
        ("ean", "EAN"),
        ("upc", "UPC"),
        ("mpn", "MPN"),
        ("weight", "Вага"),
        ("width", "Ширина"),
        ("height", "Висота"),
        ("length", "Довжина"),
        ("color", "Колір"),
        ("size", "Розмір"),
    ]

    return templates.TemplateResponse(
        "pricelist_map.html",
        {
            "request": request,
            "item": item,
            "mapping": mapping,
            "file_meta": file_meta,
            "preview_rows": preview_rows,
            "preview_errors": preview_errors,
            "custom_fields": custom_fields,
            "standard_fields": standard_fields,
        },
    )


@router.post("/ui/pricelists/{pr_id}/map")
def ui_pricelist_map_save(
    pr_id: int,
    request: Request,
    db: Session = Depends(get_db),
    # спільні поля мапінгу (для всіх форматів — колонки/літерали або теги/xpath)
    supplier_sku_type: str = Form("literal"),
    supplier_sku_value: str = Form(""),
    name_type: str = Form("literal"),
    name_value: str = Form(""),
    price_type: str = Form("literal"),
    price_value: str = Form(""),
    availability_type: str = Form("literal"),
    availability_value: str = Form(""),
    manufacturer_type: str = Form("literal"),
    manufacturer_value: str = Form(""),
    category_type: str = Form("literal"),
    category_value: str = Form(""),
    currency_type: str = Form("literal"),
    currency_value: str = Form(""),

    # пер-форматні налаштування:
    csv_encoding: str = Form("utf-8"),
    csv_delimiter: str = Form(","),
    csv_skip_rows: int = Form(1),          # ← NEW
    xlsx_sheet: str = Form("0"),
    xlsx_skip_rows: int = Form(1),         # ← NEW
    xml_container: str = Form("product"),
    xml_use_xpath: bool = Form(False),
    extra_key: List[str] = Form(default=[]),
    extra_type: List[str] = Form(default=[]),
    extra_value: List[str] = Form(default=[]),
):
    
    item = crud.get(db, pr_id)
    if not item:
        return RedirectResponse(url="/ui/pricelists", status_code=303)

    fmt = (item.format or "").lower()

    # збираємо fields
    fields = {
        "supplier_sku": {"type": supplier_sku_type, "value": supplier_sku_value},
        "name": {"type": name_type, "value": name_value},
        "price": {"type": price_type, "value": price_value},
        "availability": {"type": availability_type, "value": availability_value},
        "manufacturer": {"type": manufacturer_type, "value": manufacturer_value},
        "category": {"type": category_type, "value": category_value},
        "currency": {"type": currency_type, "value": currency_value},
        
    }

    # збираємо options залежно від формату
    options: dict = {}
    if fmt == "csv":
        options = {"encoding": csv_encoding, "delimiter": csv_delimiter, "skip_rows": max(0, int(csv_skip_rows))}
    elif fmt in ("xlsx", "xls"):
        sheet_val: int | str
        try:
            sheet_val = int(xlsx_sheet)
        except ValueError:
            sheet_val = xlsx_sheet
        options = {"sheet": sheet_val, "skip_rows": max(0, int(xlsx_skip_rows))}
    elif fmt == "xml":
        options = {"container": xml_container, "use_xpath": bool(xml_use_xpath)}

    extra: list[dict] = []
    for k, t, v in zip(extra_key, extra_type, extra_value):
        k = (k or "").strip()
        if not k:
            continue
        extra.append({"key": k, "type": t or "literal", "value": v or ""})

    mapping = {"fields": fields, "options": options, "extra": extra}

    # зберігаємо
    item.mapping = json.dumps(mapping, ensure_ascii=False)
    db.commit()
    db.refresh(item)

    # після збереження — редірект на GET із тостом
    return RedirectResponse(
        url=f"/ui/pricelists/{pr_id}/map?msg=" + quote("Мапінг збережено"),
        status_code=303,
    )
