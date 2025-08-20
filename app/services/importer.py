from __future__ import annotations

from io import BytesIO
from typing import Any

from openpyxl import load_workbook

from app.schemas.supplier_product import SupplierProductCreate


def _col_letter_to_index(letter: str) -> int:
    """A->1, B->2, Z->26, AA->27 ... (1-based)."""
    s = letter.strip().upper()
    n = 0
    for ch in s:
        if not ("A" <= ch <= "Z"):
            return 0
        n = n * 26 + (ord(ch) - ord("A") + 1)
    return n


def _to_str(v: Any) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s if s != "" else None


def _to_float(s: str | None) -> float | None:
    if s is None:
        return None
    s = s.replace(" ", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None


def _split_list(s: str | None, sep: str | None) -> list[str] | None:
    if not s or not sep:
        return None
    parts = [x.strip() for x in s.split(sep)]
    return [x for x in parts if x]


def import_xlsx_bytes(
    *,
    file_bytes: bytes,
    supplier_id: int,
    price_list_id: int,
    mapping: dict[str, Any],
    source_config: dict[str, Any] | None,
) -> tuple[list[SupplierProductCreate], list[str]]:
    """
    Підтримка by: col_letter | col_index | header_name
    source_config:
      {
        "sheet": {"by":"name","value":"Прайс"} | {"by":"index","value":1},
        "header": false,           # якщо True — читаємо імена з рядка start_row
        "start_row": 1
      }
    """
    sc = source_config or {}
    sheet_spec = sc.get("sheet") or {"by": "index", "value": 1}
    header = bool(sc.get("header", False))
    start_row = int(sc.get("start_row", 1))

    wb = load_workbook(BytesIO(file_bytes), data_only=True)
    if sheet_spec.get("by") == "name":
        ws = wb[sheet_spec.get("value")]
    else:
        idx = int(sheet_spec.get("value", 1)) - 1
        ws = wb.worksheets[idx]

    header_map: dict[str, int] = {}
    data_start = start_row
    if header:
        # будуємо мапу "header_name_lower" -> col_index (1-based)
        hdr_row = ws[start_row]
        for i, cell in enumerate(hdr_row, start=1):
            name = _to_str(cell.value)
            if name:
                header_map[name.lower()] = i
        data_start = start_row + 1

    def read_cell(row_idx: int, spec: dict[str, Any] | str | None) -> str | None:
        if not spec:
            return None
        # зворотна сумісність: просто рядок означає header_name
        if isinstance(spec, str):
            name = spec.strip().lower()
            col = header_map.get(name)
            if not col:
                return None
            return _to_str(ws.cell(row=row_idx, column=col).value)

        by = (spec.get("by") or "").strip().lower()
        if by == "col_letter":
            col = _col_letter_to_index(str(spec.get("value")))
            if col <= 0:
                return None
            return _to_str(ws.cell(row=row_idx, column=col).value)
        if by == "col_index":
            col = int(spec.get("value", 0))
            if col <= 0:
                return None
            return _to_str(ws.cell(row=row_idx, column=col).value)
        if by == "header_name":
            name = str(spec.get("value", "")).strip().lower()
            col = header_map.get(name)
            if not col:
                return None
            return _to_str(ws.cell(row=row_idx, column=col).value)
        return None

    items: list[SupplierProductCreate] = []
    errors: list[str] = []

    max_row = ws.max_row or 0
    for r in range(data_start, max_row + 1):
        try:
            supplier_sku = read_cell(r, mapping.get("supplier_sku")) or ""
            if not supplier_sku:
                # порожні рядки пропускаємо
                continue

            def opt_sep(key: str) -> str | None:
                spec = mapping.get(key) or {}
                if isinstance(spec, dict):
                    opts = spec.get("options") or {}
                    return opts.get("split")
                return None

            item = SupplierProductCreate(
                supplier_id=supplier_id,
                price_list_id=price_list_id,
                supplier_sku=supplier_sku,
                manufacturer_sku=read_cell(r, mapping.get("manufacturer_sku")),
                mpn=read_cell(r, mapping.get("mpn")),
                gtin=read_cell(r, mapping.get("gtin")),
                ean=read_cell(r, mapping.get("ean")),
                upc=read_cell(r, mapping.get("upc")),
                jan=read_cell(r, mapping.get("jan")),
                isbn=read_cell(r, mapping.get("isbn")),
                name=read_cell(r, mapping.get("name")),
                brand_raw=read_cell(r, mapping.get("brand_raw")),
                category_raw=read_cell(r, mapping.get("category_raw")),
                price_raw=_to_float(read_cell(r, mapping.get("price_raw"))),
                currency_raw=read_cell(r, mapping.get("currency_raw")),
                qty_raw=_to_float(read_cell(r, mapping.get("qty_raw"))),
                availability_text=read_cell(r, mapping.get("availability_text")),
                delivery_terms=read_cell(r, mapping.get("delivery_terms")),
                delivery_date=read_cell(r, mapping.get("delivery_date")),  # парсинг дат додамо окремо, якщо треба
                location=read_cell(r, mapping.get("location")),
                short_description_raw=read_cell(r, mapping.get("short_description_raw")),
                description_raw=read_cell(r, mapping.get("description_raw")),
                image_urls=_split_list(read_cell(r, mapping.get("image_urls")), opt_sep("image_urls")),
            )
            items.append(item)
        except Exception as e:
            errors.append(f"Row {r}: {e!r}")

    return items, errors
