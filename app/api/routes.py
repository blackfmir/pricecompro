from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

import app.crud.brand_map as brand_map_crud
import app.crud.category_map as category_map_crud

# CRUD
import app.crud.supplier_product as sp_crud
from app.crud import price_list as price_list_crud
from app.crud import supplier as supplier_crud
from app.db.session import SessionLocal

# Schemas
from app.schemas.normalize import (
    BrandMapCreate,
    BrandMapOut,
    CategoryMapCreate,
    CategoryMapOut,
    SuggestionOut,
)
from app.schemas.price_list import PriceListCreate, PriceListOut, PriceListUpdate
from app.schemas.supplier import SupplierCreate, SupplierOut, SupplierUpdate
from app.schemas.supplier_product import (
    SupplierProductCreate,
    SupplierProductOut,
    SupplierProductUpdate,
)

# Services
from app.services.importer import import_xlsx_bytes, import_xml_bytes

router = APIRouter()


# ---- DB session dependency -----------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DBSession = Annotated[Session, Depends(get_db)]
FileUpload = Annotated[UploadFile, File(...)]


# ====================== SUPPLIERS =========================================
@router.post("/suppliers", response_model=SupplierOut)
def create_supplier(db: DBSession, payload: SupplierCreate):
    return supplier_crud.create(db, payload)


@router.get("/suppliers", response_model=list[SupplierOut])
def list_suppliers(db: DBSession, q: str | None = None):
    return supplier_crud.list_(db, q=q)


@router.put("/suppliers/{supplier_id}", response_model=SupplierOut)
def update_supplier(db: DBSession, supplier_id: int, payload: SupplierUpdate):
    obj = supplier_crud.update(db, supplier_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return obj


@router.delete("/suppliers/{supplier_id}")
def delete_supplier(db: DBSession, supplier_id: int):
    ok, reason = supplier_crud.delete(db, supplier_id)
    if not ok:
        if reason == "not_found":
            raise HTTPException(status_code=404, detail="Supplier not found")
        raise HTTPException(status_code=409, detail="Cannot delete supplier with existing price lists")
    return {"ok": True}


# ====================== PRICE LISTS =======================================
@router.post("/price-lists", response_model=PriceListOut)
def create_price_list(db: DBSession, payload: PriceListCreate):
    return price_list_crud.create(db, payload)


@router.get("/price-lists", response_model=list[PriceListOut])
def list_price_lists(db: DBSession, supplier_id: int | None = None):
    return price_list_crud.list_(db, supplier_id=supplier_id)


@router.put("/price-lists/{pl_id}", response_model=PriceListOut)
def update_price_list(db: DBSession, pl_id: int, payload: PriceListUpdate):
    obj = price_list_crud.update(db, pl_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Price list not found")
    return obj


@router.delete("/price-lists/{pl_id}")
def delete_price_list(db: DBSession, pl_id: int):
    ok = price_list_crud.delete(db, pl_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Price list not found")
    return {"ok": True}


# ====================== SUPPLIER PRODUCTS =================================
@router.get("/supplier-products", response_model=dict)
def list_supplier_products(
    db: DBSession,
    supplier_id: int | None = None,
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    res = sp_crud.list_(db, supplier_id=supplier_id, q=q, limit=limit, offset=offset)
    return {
        "total": res["total"],
        "items": [SupplierProductOut.model_validate(it) for it in res["items"]],
    }


@router.put("/supplier-products/{sp_id}", response_model=SupplierProductOut)
def update_supplier_product(db: DBSession, sp_id: int, payload: SupplierProductUpdate):
    obj = sp_crud.update(db, sp_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Supplier product not found")
    return SupplierProductOut.model_validate(obj)


# ====================== IMPORT (CSV / XLSX / XML) =========================
@router.post("/import/{pl_id}")
async def import_any(pl_id: int, db: DBSession, file: FileUpload):
    pl = price_list_crud.get(db, pl_id)
    if not pl:
        raise HTTPException(status_code=404, detail="Price list not found")
    if not pl.mapping:
        raise HTTPException(status_code=400, detail="Mapping not set for this price list")

    content = await file.read()
    fmt = (pl.format or "").lower()

    items: list[SupplierProductCreate] = []
    errors: list[str] = []

    if fmt in {"xlsx", "xls"}:
        items, errors = import_xlsx_bytes(
            file_bytes=content,
            supplier_id=pl.supplier_id,
            price_list_id=pl.id,
            mapping=pl.mapping,
            source_config=pl.source_config,
        )
    elif fmt in {"xml", "yml"}:
        items, errors = import_xml_bytes(
            file_bytes=content,
            supplier_id=pl.supplier_id,
            price_list_id=pl.id,
            mapping=pl.mapping,
            source_config=pl.source_config,
        )
    elif fmt == "csv":
        import csv
        import io

        delimiter = (pl.source_config or {}).get("delimiter", ";")
        reader = csv.reader(io.StringIO(content.decode("utf-8-sig", errors="replace")), delimiter=delimiter)
        map_ = pl.mapping or {}

        def get_by_index(row: list[str], key: str):
            spec = map_.get(key)
            if not spec or not isinstance(spec, dict) or spec.get("by") != "col_index":
                return None
            idx = int(spec.get("value", 0)) - 1
            return row[idx] if 0 <= idx < len(row) else None

        def to_float(s):
            if s is None or s == "":
                return None
            s = s.replace(" ", "").replace(",", ".")
            try:
                return float(s)
            except Exception:
                return None

        def split_list(s, key):
            spec = map_.get(key) or {}
            opts = spec.get("options") or {}
            sep = opts.get("split")
            if not s or not sep:
                return None
            return [x.strip() for x in s.split(sep) if x.strip()]

        rownum = 0
        for row in reader:
            rownum += 1
            supplier_sku = (get_by_index(row, "supplier_sku") or "").strip()
            if not supplier_sku:
                continue
            try:
                items.append(
                    SupplierProductCreate(
                        supplier_id=pl.supplier_id,
                        price_list_id=pl.id,
                        supplier_sku=supplier_sku,
                        manufacturer_sku=get_by_index(row, "manufacturer_sku"),
                        mpn=get_by_index(row, "mpn"),
                        gtin=get_by_index(row, "gtin"),
                        ean=get_by_index(row, "ean"),
                        upc=get_by_index(row, "upc"),
                        jan=get_by_index(row, "jan"),
                        isbn=get_by_index(row, "isbn"),
                        name=get_by_index(row, "name"),
                        brand_raw=get_by_index(row, "brand_raw"),
                        category_raw=get_by_index(row, "category_raw"),
                        price_raw=to_float(get_by_index(row, "price_raw")),
                        currency_raw=(get_by_index(row, "currency_raw") or None),
                        qty_raw=to_float(get_by_index(row, "qty_raw")),
                        availability_text=get_by_index(row, "availability_text"),
                        delivery_terms=get_by_index(row, "delivery_terms"),
                        delivery_date=get_by_index(row, "delivery_date"),
                        location=get_by_index(row, "location"),
                        short_description_raw=get_by_index(row, "short_description_raw"),
                        description_raw=get_by_index(row, "description_raw"),
                        image_urls=split_list(get_by_index(row, "image_urls"), "image_urls"),
                    )
                )
            except Exception as e:
                errors.append(f"Row {rownum}: {e!r}")
    else:
        raise HTTPException(status_code=501, detail=f"Import for format '{fmt}' not implemented yet")

    stats = sp_crud.upsert_many(db, items)

    # NEW: автонормалізація відразу після імпорту
    brand_map_crud.apply_to_products(db, pl.supplier_id)
    category_map_crud.apply_to_products(db, pl.supplier_id)

    return {
        "price_list_id": pl.id,
        "format": fmt,
        "stats": stats,
        "errors": errors[:10],
        "preview": [i.model_dump() for i in items[:5]],
    }


# (залишаємо короткий сумісний шлях для CSV)
@router.post("/import/{pl_id}/csv")
async def import_csv(pl_id: int, db: DBSession, file: FileUpload):
    return await import_any(pl_id, db, file)


# ====================== NORMALIZATION =====================================
@router.get("/normalize/brand-suggestions", response_model=list[SuggestionOut])
def brand_suggestions(db: DBSession, supplier_id: int, limit: int = 100):
    return brand_map_crud.suggestions(db, supplier_id, limit)


@router.get("/normalize/category-suggestions", response_model=list[SuggestionOut])
def category_suggestions(db: DBSession, supplier_id: int, limit: int = 100):
    return category_map_crud.suggestions(db, supplier_id, limit)

@router.post("/category-maps", response_model=CategoryMapOut)
def create_category_map(db: DBSession, payload: CategoryMapCreate):
    return category_map_crud.create(db, payload.supplier_id, payload.raw_name, payload.category_id)


@router.put("/category-maps/{cm_id}", response_model=CategoryMapOut)
def update_category_map(db: DBSession, cm_id: int, category_id: int):
    obj = category_map_crud.update(db, cm_id, category_id)
    if not obj:
        raise HTTPException(404, "Category map not found")
    return obj

@router.delete("/category-maps/{cm_id}")
def delete_category_map(db: DBSession, cm_id: int):
    ok = category_map_crud.delete(db, cm_id)
    if not ok:
        raise HTTPException(404, "Category map not found")
    return {"ok": True}

@router.post("/brand-maps", response_model=BrandMapOut)
def create_brand_map(db: DBSession, payload: BrandMapCreate):
    return brand_map_crud.create(db, payload.supplier_id, payload.raw_name, payload.manufacturer_id)

@router.put("/brand-maps/{bm_id}", response_model=BrandMapOut)
def update_brand_map(db: DBSession, bm_id: int, manufacturer_id: int):
    obj = brand_map_crud.update(db, bm_id, manufacturer_id)
    if not obj:
        raise HTTPException(404, "Brand map not found")
    return obj

@router.delete("/brand-maps/{bm_id}")
def delete_brand_map(db: DBSession, bm_id: int):
    ok = brand_map_crud.delete(db, bm_id)
    if not ok:
        raise HTTPException(404, "Brand map not found")
    return {"ok": True}

@router.post("/normalize/apply")
def apply_maps(db: DBSession, supplier_id: int):
    updated_brands = brand_map_crud.apply_to_products(db, supplier_id)
    updated_categories = category_map_crud.apply_to_products(db, supplier_id)
    return {
        "supplier_id": supplier_id,
        "updated_brands": updated_brands,
        "updated_categories": updated_categories,
    }
