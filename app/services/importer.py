from __future__ import annotations
from io import BytesIO
from typing import Tuple, Any, Iterable

import pandas as pd
from lxml import etree


def _norm_str(v: Any) -> str:
    if v is None:
        return ""
    s = str(v).strip()
    return s


def _col_value(row: pd.Series, idx1: int) -> str:
    """Забирає значення з 1-базною колонки."""
    i = max(1, int(idx1)) - 1
    if i < 0 or i >= len(row):
        return ""
    return _norm_str(row.iloc[i])


def preview_csv_bytes(*, data: bytes, mapping: dict, source_config: dict, limit: int = 20) -> Tuple[list[dict], list[str]]:
    sc = source_config or {}
    enc = _normalize_encoding(sc.get("encoding", "utf-8"))  # якщо додавали нормалізацію
    raw_delim = sc.get("delimiter", ",")
    delim = _resolve_delimiter(raw_delim)  # якщо додавали підтримку \t/auto
    skip_rows = max(0, int(sc.get("skip_rows", 1)))
    errors: list[str] = []

    try:
        if delim is None:  # auto-detect
            df = pd.read_csv(BytesIO(data), encoding=enc, sep=None, engine="python",
                             header=None, dtype=str, keep_default_na=False, skiprows=skip_rows)
        else:
            df = pd.read_csv(BytesIO(data), encoding=enc, sep=delim,
                             header=None, dtype=str, keep_default_na=False, skiprows=skip_rows)
    except Exception as e:
        return [], [f"CSV read error: {e}"]

    fields = mapping.get("fields", {})
    rows: list[dict] = []
    for _, row in df.head(limit).iterrows():
        item: dict[str, Any] = {}
        for fname, spec in fields.items():
            ftype = spec.get("type", "literal")
            val = spec.get("value", "")
            if ftype == "col":
                try:
                    item[fname] = _col_value(row, int(val))
                except Exception:
                    item[fname] = ""
                    errors.append(f"Bad column index for field '{fname}': {val}")
            elif ftype == "literal":
                item[fname] = _norm_str(val)
            else:
                item[fname] = ""
                errors.append(f"Unsupported field type for CSV: {ftype}")
        rows.append(item)
    return rows, errors


def preview_xlsx_bytes(*, data: bytes, mapping: dict, source_config: dict, limit: int = 20) -> Tuple[list[dict], list[str]]:
    sc = source_config or {}
    sheet = sc.get("sheet", 0)
    skip_rows = max(0, int(sc.get("skip_rows", 1)))
    errors: list[str] = []
    try:
        df = pd.read_excel(BytesIO(data), sheet_name=sheet, header=None, dtype=str, skiprows=skip_rows)
        if isinstance(df, dict):
            df = next(iter(df.values()))
        df = df.fillna("")
    except Exception as e:
        return [], [f"XLSX read error: {e}"]

    fields = mapping.get("fields", {})
    rows: list[dict] = []
    for _, row in df.head(limit).iterrows():
        item: dict[str, Any] = {}
        for fname, spec in fields.items():
            ftype = spec.get("type", "literal")
            val = spec.get("value", "")
            if ftype == "col":
                try:
                    item[fname] = _col_value(row, int(val))
                except Exception:
                    item[fname] = ""
                    errors.append(f"Bad column index for field '{fname}': {val}")
            elif ftype == "literal":
                item[fname] = _norm_str(val)
            else:
                item[fname] = ""
                errors.append(f"Unsupported field type for XLSX: {ftype}")
        rows.append(item)
    return rows, errors


def _iter_xml_items(root: etree._Element, container: str, use_xpath: bool) -> Iterable[etree._Element]:
    if use_xpath:
        return root.xpath(container)
    # простий варіант: усі елементи з тегом container у глибині
    return root.findall(f".//{container}")


def preview_xml_bytes(
    *, data: bytes, mapping: dict, source_config: dict, limit: int = 20
) -> Tuple[list[dict], list[str]]:
    sc = source_config or {}
    container = sc.get("container", "product")
    use_xpath = bool(sc.get("use_xpath", False))
    errors: list[str] = []

    try:
        root = etree.fromstring(data)
    except Exception as e:
        return [], [f"XML parse error: {e}"]

    fields = mapping.get("fields", {})
    rows: list[dict] = []
    for i, elem in enumerate(_iter_xml_items(root, container, use_xpath)):
        if i >= limit:
            break
        item: dict[str, Any] = {}
        for fname, spec in fields.items():
            ftype = spec.get("type", "literal")
            val = spec.get("value", "")
            if ftype == "tag":
                # дочірній тег за ім’ям
                child = elem.find(val)
                item[fname] = _norm_str(child.text if child is not None else "")
            elif ftype == "xpath":
                # відносний xpath від elem
                try:
                    nodes = elem.xpath(val)
                    if nodes:
                        node = nodes[0]
                        if isinstance(node, etree._Element):
                            item[fname] = _norm_str(node.text)
                        else:
                            item[fname] = _norm_str(node)
                    else:
                        item[fname] = ""
                except Exception:
                    item[fname] = ""
                    errors.append(f"Bad xpath for field '{fname}': {val}")
            elif ftype == "literal":
                item[fname] = _norm_str(val)
            else:
                item[fname] = ""
                errors.append(f"Unsupported field type for XML: {ftype}")
        rows.append(item)
    return rows, errors


# ---- Загальний попередній перегляд із файлу ----
def preview_from_file(*, data: bytes, fmt: str, mapping: dict, source_config: dict, limit: int = 20) -> Tuple[list[dict], list[str]]:
    fmt = (fmt or "").lower()
    if fmt in ("csv",):
        return preview_csv_bytes(data=data, mapping=mapping, source_config=source_config, limit=limit)
    if fmt in ("xlsx", "xls"):
        return preview_xlsx_bytes(data=data, mapping=mapping, source_config=source_config, limit=limit)
    if fmt in ("xml",):
        return preview_xml_bytes(data=data, mapping=mapping, source_config=source_config, limit=limit)
    return [], [f"Unsupported format for preview: {fmt}"]


# Плейсхолдери імпорту (наступний етап оновить їх для запису у БД)
def import_xlsx_bytes(*, data: bytes, supplier_id: int, pricelist_id: int, mapping: dict, source_config: dict) -> Tuple[list[dict], list[str], dict]:
    items, errors = preview_xlsx_bytes(data=data, mapping=mapping, source_config=source_config, limit=10_000)
    return items, errors, {"inserted": 0, "updated": 0}

def import_csv_bytes(*, data: bytes, supplier_id: int, pricelist_id: int, mapping: dict, source_config: dict) -> Tuple[list[dict], list[str], dict]:
    items, errors = preview_csv_bytes(data=data, mapping=mapping, source_config=source_config, limit=10_000)
    return items, errors, {"inserted": 0, "updated": 0}

def import_xml_bytes(*, data: bytes, supplier_id: int, pricelist_id: int, mapping: dict, source_config: dict) -> Tuple[list[dict], list[str], dict]:
    items, errors = preview_xml_bytes(data=data, mapping=mapping, source_config=source_config, limit=10_000)
    return items, errors, {"inserted": 0, "updated": 0}

def _resolve_delimiter(s: str | None) -> str | None:
    if s is None:
        return ","
    v = str(s).strip()
    low = v.lower()
    # табуляція
    if low in ("\\t", "tab", "tsv", "\\x09", "0x09"):
        return "\t"
    # пробіл
    if low in ("space", "\\s"):
        return " "
    # авто-розпізнавання
    if low in ("auto", "detect"):
        return None  # sep=None -> pandas авто-детект із engine='python'
    # hex-код символу
    if low.startswith("0x"):
        try:
            return chr(int(low, 16))
        except Exception:
            return v
    return v

def _normalize_encoding(enc: str | None) -> str:
    if not enc:
        return "utf-8"
    e = enc.strip().lower().replace("_", "-")
    if e in ("utf8", "utf-8"):
        return "utf-8"
    if e in ("utf8-bom", "utf-8-bom", "utf-8 with bom", "utf-8-sig"):
        return "utf-8-sig"
    if e in ("win1251", "cp1251", "windows-1251"):
        return "cp1251"
    return enc

def _parse_price(v: Any) -> float | None:
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    # простенький парсер: прибираємо пробіли, замінимо кому на крапку
    s = s.replace(" ", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None

def to_supplier_products(rows: list[dict]) -> list[dict]:
    """Перекладає розпарсені поля в структуру для supplier_products."""
    out: list[dict] = []
    for r in rows:
        out.append({
            "supplier_sku": r.get("supplier_sku", "") or "",
            "name": r.get("name", "") or "",
            "price_raw": _parse_price(r.get("price")),
            "currency_raw": (r.get("currency") or "").upper() if r.get("currency") else None,
            "availability_raw": r.get("availability"),
            "manufacturer_raw": r.get("manufacturer"),
            "category_raw": r.get("category"),
        })
    return out
