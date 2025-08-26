from __future__ import annotations
from typing import Any, Iterable
import time, re, json
import requests
from bs4 import BeautifulSoup, Tag  # NEW
from lxml import html, etree
from app.utils.storage import save_upload
from datetime import datetime
from urllib.parse import urljoin
from io import StringIO
import csv




DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PriceComProBot/0.1"

def _sse(event: dict) -> str:
    """Формує один SSE-пакет (без іменованих подій, тільки data)."""
    import json as _json
    return "data: " + _json.dumps(event, ensure_ascii=False) + "\n\n"

def stream_scraper(*, scraper: dict, pricelist_id: int | None, db_settings: dict) -> Iterable[bytes]:
    """
    Генерує SSE-події під час краулінгу/парсингу/експорту.
    Події:
      {"type":"log","message":"..."}
      {"type":"progress","phase":"crawl","pages_done":..,"queue":..,"products":..}
      {"type":"progress","phase":"products","done":..,"total":..}
      {"type":"done","file_url":"...","rel_path":"...","stats":{"products":N,"pages":M}}
      {"type":"error","message":"..."}
    """
    try:
        settings = scraper.get("settings") or {}
        rules = scraper.get("rules") or {}
        categories = rules.get("categories") or {}
        listing = rules.get("listing") or {}
        product = rules.get("product") or {}

        ua = settings.get("user_agent") or DEFAULT_UA
        try:
            delay = float(settings.get("delay") or 0)
        except Exception:
            delay = 0.0

        start_urls: list[str] = scraper.get("start_urls") or []
        if not start_urls:
            yield _sse({"type": "error", "message": "Немає стартових URL."}).encode("utf-8")
            return

        yield _sse({"type": "log", "message": f"Початок. Стартові URL: {len(start_urls)}"}).encode("utf-8")

        # 1) початкові посилання: стартові + (за наявності) категорії зі стартових
        queue: list[str] = []
        visited_pages: set[str] = set()
        product_links: set[str] = set()

        # Додаємо стартові в чергу
        for u in start_urls:
            queue.append(u)

        # Розширюємо категоріями зі стартових (одноразово)
        if categories.get("link_selectors"):
            cat_found = 0
            for u in list(start_urls):
                try:
                    final_u, content = _fetch(u, ua=ua)
                    doc, soup = _parse_docs(content)
                    for sel in categories.get("link_selectors", []):
                        isx = bool(sel.get("is_xpath"))
                        s = sel.get("selector", "") or ""
                        for el in _select(doc, soup, s, is_xpath=isx):
                            href = el.get("href") if hasattr(el, "get") else None
                            if not href and hasattr(el, "get"):
                                href = el.get("src")
                            if href:
                                abs_u = urljoin(final_u, href)
                                if abs_u not in queue:
                                    queue.append(abs_u)
                                    cat_found += 1
                    time.sleep(delay)
                except Exception:
                    continue
            yield _sse({"type":"log","message":f"Додано категорійних посилань: {cat_found}"}).encode("utf-8")

        # 2) обхід сторінок: збір посилань на товари + пагінація
        pages_done = 0
        while queue:
            url = queue.pop(0)
            if url in visited_pages:
                continue
            visited_pages.add(url)
            try:
                final_url, content = _fetch(url, ua=ua)
                doc, soup = _parse_docs(content)

                # посилання на товари
                for sel in listing.get("product_link_selectors", []):
                    isx = bool(sel.get("is_xpath"))
                    s = sel.get("selector", "") or ""
                    for el in _select(doc, soup, s, is_xpath=isx):
                        href = el.get("href") if hasattr(el, "get") else None
                        if not href and hasattr(el, "get"):
                            href = el.get("src")
                        if href:
                            product_links.add(urljoin(final_url, href))

                # пагінація (лістинг)
                for sel in listing.get("pagination", []):
                    isx = bool(sel.get("is_xpath"))
                    s = sel.get("selector", "") or ""
                    for el in _select(doc, soup, s, is_xpath=isx):
                        href = el.get("href") if hasattr(el, "get") else None
                        if not href and hasattr(el, "get"):
                            href = el.get("src")
                        if href:
                            next_u = urljoin(final_url, href)
                            if next_u not in visited_pages and next_u not in queue:
                                queue.append(next_u)

                pages_done += 1
                if pages_done % 3 == 0:
                    yield _sse({
                        "type": "progress",
                        "phase": "crawl",
                        "pages_done": pages_done,
                        "queue": len(queue),
                        "products": len(product_links)
                    }).encode("utf-8")
            except Exception as e:
                yield _sse({"type":"log","message":f"Помилка сторінки: {url} — {e}"}).encode("utf-8")
                continue
            finally:
                time.sleep(delay)

        yield _sse({"type":"log","message":f"Збір посилань завершено. Товарів: {len(product_links)}, сторінок: {pages_done}"}).encode("utf-8")

        # 3) картки товарів
        items: list[dict[str, Any]] = []
        total = len(product_links)
        done = 0

        for link in sorted(product_links):
            try:
                final, bytes_ = _fetch(link, ua=ua)
                base_url = final
                doc, soup = _parse_docs(bytes_)

                row: dict[str, Any] = {}
                # --- поля ---
                for fld in (product.get("fields") or []):
                    key = (fld.get("key") or "").strip()
                    if not key:
                        continue

                    sel = fld.get("selector", "") or ""
                    isx = bool(fld.get("is_xpath"))
                    as_list = bool(fld.get("as_list"))
                    sep = fld.get("sep") or ", "

                    get_html = bool(fld.get("get_html"))
                    inner_html = bool(fld.get("inner_html"))
                    allowed = [t.strip() for t in (fld.get("allowed_tags") or "").split(",") if t.strip()]
                    rm_links = bool(fld.get("remove_links"))

                    regex   = fld.get("regex") or None
                    deltxt  = fld.get("delete_text") or None
                    findt   = fld.get("find") or None
                    rept    = fld.get("replace") or None

                    attr = (fld.get("attr") or "").strip()
                    make_abs = bool(fld.get("make_absolute"))

                    elems = _select(doc, soup, sel, is_xpath=isx) if sel else []

                    def extract_val(e) -> str:
                        if attr:
                            try:
                                v = e.get(attr) if hasattr(e, "get") else None
                            except Exception:
                                v = None
                            v = v or ""
                            if make_abs and v:
                                v = urljoin(base_url, v)
                            return _apply_text_ops(v, regex=regex, delete_text=deltxt, find_text=findt, replace_text=rept)

                        raw = _norm_html(
                            e,
                            get_html=get_html,
                            inner_html=inner_html,
                            allowed_tags=allowed,
                            remove_links=rm_links
                        )
                        return _apply_text_ops(raw, regex=regex, delete_text=deltxt, find_text=findt, replace_text=rept)

                    if as_list:
                        vals = [extract_val(e) for e in elems]
                        row[key] = sep.join([v for v in vals if v])
                    else:
                        v = extract_val(elems[0]) if elems else ""
                        row[key] = v

                # --- атрибути (за наявності правил) ---
                attrs = (product.get("attributes") or None)
                if attrs:
                    import json as _json
                    key = (attrs.get("key") or "attributes").strip() or "attributes"

                    c = attrs.get("container") or {}
                    n = attrs.get("name") or {}
                    v = attrs.get("value") or {}
                    c_sel, c_xp = c.get("selector", ""), bool(c.get("is_xpath"))
                    n_sel, n_xp = n.get("selector", ""), bool(n.get("is_xpath"))
                    v_sel, v_xp = v.get("selector", ""), bool(v.get("is_xpath"))
                    v_sep = v.get("sep") or ", "

                    if c_sel and n_sel and v_sel:
                        specs: dict[str, str] = {}
                        containers = _select(doc, soup, c_sel, is_xpath=c_xp)
                        for cont in containers:
                            name_nodes = _select_within(cont, n_sel, is_xpath=n_xp)
                            name_text = ""
                            if name_nodes:
                                name_text = _norm_html(name_nodes[0], get_html=False)
                            if not name_text:
                                continue

                            val_nodes = _select_within(cont, v_sel, is_xpath=v_xp)
                            vals: list[str] = []
                            for vn in val_nodes:
                                vals.append(_norm_html(vn, get_html=False))
                            val_text = v_sep.join([t for t in (v.strip() for v in vals) if t])
                            if val_text:
                                specs[name_text.strip()] = val_text

                        if specs:
                            row[key] = _json.dumps(specs, ensure_ascii=False)

                items.append(row)

            except Exception as e:
                yield _sse({"type":"log","message":f"Помилка картки: {link} — {e}"}).encode("utf-8")
                # продовжуємо
            finally:
                done += 1
                if done % 5 == 0 or done == total:
                    yield _sse({"type":"progress","phase":"products","done":done,"total":total}).encode("utf-8")
                time.sleep(delay)

        # 4) експорт у CSV
        base_cols = ["supplier_sku", "name", "price", "currency", "availability", "manufacturer", "category", "image_urls"]
        keys = set()
        for r in items:
            keys.update(r.keys())
        cols = base_cols + [k for k in sorted(keys) if k not in base_cols]

        buf = StringIO()
        w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore", delimiter=";")
        w.writeheader()
        for r in items:
            w.writerow(r)
        csv_bytes = buf.getvalue().encode("utf-8-sig")

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"scrape_{ts}.csv"
        rel, url = save_upload(f"pricelists/{pricelist_id or 'no_pl'}/generated", fname, csv_bytes)

        yield _sse({
            "type":"done",
            "file_url": url,
            "rel_path": rel,
            "stats": {"products": len(items), "pages": pages_done}
        }).encode("utf-8")

    except Exception as e:
        yield _sse({"type":"error","message": f"Фатальна помилка: {e}"}).encode("utf-8")

def _fetch(url: str, *, ua: str | None = None, proxies: list[str] | None = None, timeout: int = 30) -> tuple[str, bytes]:
    headers = {"User-Agent": ua or DEFAULT_UA}
    proxy = None
    if proxies:
        proxy = proxies[0]  # MVP: один проксі
    resp = requests.get(url, headers=headers, proxies={"http": proxy, "https": proxy} if proxy else None, timeout=timeout)
    resp.raise_for_status()
    return resp.url, resp.content

def _norm_html(elem, *, get_html: bool, inner_html: bool = False,
               allowed_tags: list[str] | None = None, remove_links: bool = False) -> str:
    """
    Повертає:
      - якщо get_html=True і inner_html=False: outer HTML елемента
      - якщо get_html=True і inner_html=True:  inner HTML елемента (без самого контейнера)
      - якщо get_html=False: plain text
    Працює і для bs4.Tag, і для lxml-елементів.
    """
    # --- BeautifulSoup.Tag ---
    if isinstance(elem, Tag):
        if get_html:
            from bs4 import BeautifulSoup
            frag = BeautifulSoup(str(elem), "html.parser")
            top = next((c for c in frag.contents if isinstance(c, Tag)), None)
            if top is None:
                return ""
            if top.name in ("html", "body"):
                inner_top = next((c for c in top.contents if isinstance(c, Tag)), None)
                if inner_top:
                    top = inner_top

            if remove_links:
                for a in top.find_all("a"):
                    a.unwrap()

            if allowed_tags:
                allow = set(allowed_tags)
                for t in list(top.find_all(True)):
                    if t is top:
                        continue
                    if t.name not in allow:
                        t.unwrap()

            if inner_html:
                # Внутрішній HTML (вміст без контейнера)
                return "".join(str(c) for c in top.contents).strip()

            # Зовнішній HTML (разом із контейнером)
            return top.decode().strip()

        return elem.get_text(" ", strip=True)

    # --- lxml елементи ---
    if get_html:
        from lxml import etree, html
        clone = html.fromstring(etree.tostring(elem, encoding="unicode"))

        if remove_links:
            for a in clone.xpath(".//a"):
                a.drop_tag()

        if allowed_tags:
            allow = set(allowed_tags)
            for e in list(clone.iter()):
                if isinstance(e.tag, str) and e is not clone and e.tag not in allow:
                    e.drop_tag()

        if inner_html:
            # Внутрішній HTML: текст + дочірні вузли (із tail)
            parts: list[str] = []
            if clone.text:
                parts.append(clone.text)
            for child in clone:
                parts.append(etree.tostring(child, encoding="unicode", with_tail=False))
                if child.tail:
                    parts.append(child.tail)
            return "".join(parts).strip()

        # Зовнішній HTML
        return etree.tostring(clone, encoding="unicode", with_tail=False).strip()

    return (elem.text_content() if hasattr(elem, "text_content") else str(elem)).strip()



def _select(doc: html.HtmlElement, selector: str, *, is_xpath: bool) -> list[etree._Element]:
    return (doc.xpath(selector) if is_xpath else doc.cssselect(selector))  # type: ignore

def _apply_text_ops(val: str, *, regex: str | None, delete_text: str | None, find_text: str | None, replace_text: str | None) -> str:
    s = val or ""
    if regex:
        m = re.findall(regex, s, flags=re.I | re.M | re.S)
        s = " ".join(m) if m else ""
    if delete_text:
        s = s.replace(delete_text, "")
    if find_text is not None and replace_text is not None:
        s = s.replace(find_text, replace_text)
    return s.strip()

def preview_block(url: str, *, rules: dict, ua: str | None = None, delay: float = 0.0) -> dict:
    """
    Прев'ю результатів для одного URL і одного блоку правил:
      kind = "categories" | "listing" | "product"
    Повертає: {"url": ..., "html": ..., "items": [...], "errors": [...]}
    """
    final_url, content = _fetch(url, ua=ua)
    base_url = final_url
    doc, soup = _parse_docs(content)

    errors: list[str] = []
    out: list[Any] = []
    kind = rules.get("kind")  # "categories"|"listing"|"product"

    if kind in ("categories", "listing"):
        # Збір посилань і пагінації
        links: list[str] = []
        nexts: list[str] = []

        link_sets = []
        if "link_selectors" in rules:
            link_sets.extend(rules.get("link_selectors", []))
        if "product_link_selectors" in rules:
            link_sets.extend(rules.get("product_link_selectors", []))

        for sel in link_sets:
            isx = bool(sel.get("is_xpath"))
            s = sel.get("selector", "") or ""
            for el in _select(doc, soup, s, is_xpath=isx):
                try:
                    href = el.get("href") if hasattr(el, "get") else None
                    if not href and hasattr(el, "get"):
                        href = el.get("src")
                except Exception:
                    href = None
                if href:
                    links.append(urljoin(base_url, href))

        for sel in rules.get("pagination", []):
            isx = bool(sel.get("is_xpath"))
            s = sel.get("selector", "") or ""
            for el in _select(doc, soup, s, is_xpath=isx):
                try:
                    href = el.get("href") if hasattr(el, "get") else None
                    if not href and hasattr(el, "get"):
                        href = el.get("src")
                except Exception:
                    href = None
                if href:
                    nexts.append(urljoin(base_url, href))

        out = [{"links": links, "next_pages": nexts}]

    else:
        # Картка товару: поля
        row: dict[str, Any] = {}
        for fld in rules.get("fields", []):
            key = (fld.get("key") or "").strip()
            if not key:
                continue

            sel = fld.get("selector", "") or ""
            isx = bool(fld.get("is_xpath"))
            as_list = bool(fld.get("as_list"))
            sep = fld.get("sep") or ", "

            get_html = bool(fld.get("get_html"))
            inner_html = bool(fld.get("inner_html"))  # NEW
            allowed = [t.strip() for t in (fld.get("allowed_tags") or "").split(",") if t.strip()]
            rm_links = bool(fld.get("remove_links"))

            regex   = fld.get("regex") or None
            deltxt  = fld.get("delete_text") or None
            findt   = fld.get("find") or None
            rept    = fld.get("replace") or None

            attr = (fld.get("attr") or "").strip()
            make_abs = bool(fld.get("make_absolute"))

            elems = _select(doc, soup, sel, is_xpath=isx) if sel else []

            def extract_val(e) -> str:
                # Пріоритет — атрибут, якщо задано
                if attr:
                    try:
                        v = e.get(attr) if hasattr(e, "get") else None
                    except Exception:
                        v = None
                    v = v or ""
                    if make_abs and v:
                        v = urljoin(base_url, v)
                    return _apply_text_ops(v, regex=regex, delete_text=deltxt, find_text=findt, replace_text=rept)

                # HTML або plain text елемента
                raw = _norm_html(
                    e,
                    get_html=get_html,
                    inner_html=inner_html,         # NEW
                    allowed_tags=allowed,
                    remove_links=rm_links
                )
                return _apply_text_ops(raw, regex=regex, delete_text=deltxt, find_text=findt, replace_text=rept)

            if as_list:
                vals = [extract_val(e) for e in elems]
                row[key] = sep.join([v for v in vals if v])
            else:
                v = extract_val(elems[0]) if elems else ""
                row[key] = v
        attrs = (rules.get("attributes") or None)
        if attrs:
            import json as _json
            key = (attrs.get("key") or "attributes").strip() or "attributes"

            c = attrs.get("container") or {}
            n = attrs.get("name") or {}
            v = attrs.get("value") or {}
            c_sel, c_xp = c.get("selector", ""), bool(c.get("is_xpath"))
            n_sel, n_xp = n.get("selector", ""), bool(n.get("is_xpath"))
            v_sel, v_xp = v.get("selector", ""), bool(v.get("is_xpath"))
            v_sep = v.get("sep") or ", "

            if c_sel and n_sel and v_sel:
                specs: dict[str, str] = {}
                containers = _select(doc, soup, c_sel, is_xpath=c_xp)
                for cont in containers:
                    # знайти назву всередині контейнера
                    name_nodes = _select_within(cont, n_sel, is_xpath=n_xp)
                    name_text = ""
                    if name_nodes:
                        name_text = _norm_html(name_nodes[0], get_html=False)

                    if not name_text:
                        continue

                    # знайти значення (може бути кілька)
                    val_nodes = _select_within(cont, v_sel, is_xpath=v_xp)
                    vals: list[str] = []
                    for vn in val_nodes:
                        vals.append(_norm_html(vn, get_html=False))
                    val_text = v_sep.join([t for t in (v.strip() for v in vals) if t])

                    if val_text:
                        specs[name_text.strip()] = val_text

                # зберігаємо JSON-рядком
                if specs:
                    row[key] = _json.dumps(specs, ensure_ascii=False)
        out = [row]

    return {
        "url": final_url,
        "html": content.decode("utf-8", errors="ignore"),
        "items": out,
        "errors": errors,
    }


def run_scraper_to_csv(*, scraper: dict, pricelist_id: int | None, db_settings: dict) -> tuple[str, str]:
    """
    Проходить стартові URL як лістинги, збирає лінки на товари, тягне картки і зберігає CSV.
    Підтримує поля з attr (href/src/data-*) та make_absolute, а також inner_html.
    """
    ua = (scraper.get("settings") or {}).get("user_agent") or DEFAULT_UA
    try:
        delay = float((scraper.get("settings") or {}).get("delay") or 0)
    except Exception:
        delay = 0.0

    rules = scraper.get("rules") or {}
    start_urls = scraper.get("start_urls") or []

    listing = rules.get("listing") or {}
    product = rules.get("product") or {}

    items: list[dict[str, Any]] = []

    # 1) Збір посилань на товари з лістингів
    product_links: set[str] = set()
    for u in start_urls:
        final_url, content = _fetch(u, ua=ua)
        base_url = final_url
        doc, soup = _parse_docs(content)

        for sel in listing.get("product_link_selectors", []):
            isx = bool(sel.get("is_xpath"))
            selector = sel.get("selector", "") or ""
            for el in _select(doc, soup, selector, is_xpath=isx):
                try:
                    href = el.get("href") if hasattr(el, "get") else None
                    if not href and hasattr(el, "get"):
                        href = el.get("src")
                except Exception:
                    href = None
                if href:
                    product_links.add(urljoin(base_url, href))

        time.sleep(delay)

    # 2) Картки товарів
    for link in product_links:
        try:
            final, bytes_ = _fetch(link, ua=ua)
            base_url = final
            doc, soup = _parse_docs(bytes_)

            row: dict[str, Any] = {}
            for fld in product.get("fields", []):
                key = (fld.get("key") or "").strip()
                if not key:
                    continue

                sel = fld.get("selector", "") or ""
                isx = bool(fld.get("is_xpath"))
                as_list = bool(fld.get("as_list"))
                sep = fld.get("sep") or ", "

                get_html = bool(fld.get("get_html"))
                inner_html = bool(fld.get("inner_html"))  # NEW
                allowed = [t.strip() for t in (fld.get("allowed_tags") or "").split(",") if t.strip()]
                rm_links = bool(fld.get("remove_links"))

                regex   = fld.get("regex") or None
                deltxt  = fld.get("delete_text") or None
                findt   = fld.get("find") or None
                rept    = fld.get("replace") or None

                attr = (fld.get("attr") or "").strip()
                make_abs = bool(fld.get("make_absolute"))

                elems = _select(doc, soup, sel, is_xpath=isx) if sel else []

                def extract_val(e) -> str:
                    if attr:
                        try:
                            v = e.get(attr) if hasattr(e, "get") else None
                        except Exception:
                            v = None
                        v = v or ""
                        if make_abs and v:
                            v = urljoin(base_url, v)
                        return _apply_text_ops(v, regex=regex, delete_text=deltxt, find_text=findt, replace_text=rept)

                    raw = _norm_html(
                        e,
                        get_html=get_html,
                        inner_html=inner_html,      # NEW
                        allowed_tags=allowed,
                        remove_links=rm_links
                    )
                    return _apply_text_ops(raw, regex=regex, delete_text=deltxt, find_text=findt, replace_text=rept)

                if as_list:
                    vals = [extract_val(e) for e in elems]
                    row[key] = sep.join([v for v in vals if v])
                else:
                    v = extract_val(elems[0]) if elems else ""
                    row[key] = v

            # --- Атрибути (таблиця характеристик) ---
            attrs = (product.get("attributes") or None)
            if attrs:
                import json as _json
                key = (attrs.get("key") or "attributes").strip() or "attributes"

                c = attrs.get("container") or {}
                n = attrs.get("name") or {}
                v = attrs.get("value") or {}
                c_sel, c_xp = c.get("selector", ""), bool(c.get("is_xpath"))
                n_sel, n_xp = n.get("selector", ""), bool(n.get("is_xpath"))
                v_sel, v_xp = v.get("selector", ""), bool(v.get("is_xpath"))
                v_sep = v.get("sep") or ", "

                if c_sel and n_sel and v_sel:
                    specs: dict[str, str] = {}
                    containers = _select(doc, soup, c_sel, is_xpath=c_xp)
                    for cont in containers:
                        name_nodes = _select_within(cont, n_sel, is_xpath=n_xp)
                        name_text = ""
                        if name_nodes:
                            name_text = _norm_html(name_nodes[0], get_html=False)
                        if not name_text:
                            continue

                        val_nodes = _select_within(cont, v_sel, is_xpath=v_xp)
                        vals: list[str] = []
                        for vn in val_nodes:
                            vals.append(_norm_html(vn, get_html=False))
                        val_text = v_sep.join([t for t in (v.strip() for v in vals) if t])

                        if val_text:
                            specs[name_text.strip()] = val_text

                    if specs:
                        row[key] = _json.dumps(specs, ensure_ascii=False)
            items.append(row)

        except Exception:
            # Проблемна картка не зупиняє весь процес
            continue

        time.sleep(delay)

    # 3) Запис CSV (UTF-8 BOM) з ; як роздільником
    base_cols = ["supplier_sku", "name", "price", "currency", "availability", "manufacturer", "category", "image_urls"]

    keys = set()
    for r in items:
        keys.update(r.keys())
    cols = base_cols + [k for k in sorted(keys) if k not in base_cols]

    buf = StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore", delimiter=";")
    w.writeheader()
    for r in items:
        w.writerow(r)
    csv_bytes = buf.getvalue().encode("utf-8-sig")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"scrape_{ts}.csv"

    rel, url = save_upload(f"pricelists/{pricelist_id or 'no_pl'}/generated", fname, csv_bytes)
    return rel, url


def _parse_docs(content: bytes) -> tuple[html.HtmlElement, BeautifulSoup]:
    """Розбираємо сторінку і як lxml, і як BeautifulSoup."""
    doc = html.fromstring(content)
    soup = BeautifulSoup(content, "lxml")
    return doc, soup

def _select(doc: html.HtmlElement, soup: BeautifulSoup, selector: str, *, is_xpath: bool):
    """Єдиний вхід для вибірок: XPath через lxml, CSS через bs4. Помилки селектора не падають."""
    if not selector:
        return []
    try:
        if is_xpath:
            return doc.xpath(selector)
        # CSS:
        return list(soup.select(selector))
    except Exception:
        return []
    
def _select_within(container, selector: str, *, is_xpath: bool):
    """
    Вибирає елементи всередині конкретного контейнера.
    Підтримує:
      - CSS (через BeautifulSoup .select)
      - XPath (через lxml .xpath, відносний; якщо селектор не починається з '.', додамо префікс '.').
    Повертає список елементів (bs4.Tag або lxml елементи).
    """
    if not selector:
        return []

    if is_xpath:
        # lxml шлях
        if isinstance(container, Tag):
            node = html.fromstring(str(container))
        else:
            node = container
        xp = selector
        if not xp.startswith("."):
            # зробимо відносним
            if xp.startswith("//"):
                xp = "." + xp
            elif xp.startswith("/"):
                xp = "." + xp
            else:
                xp = ".//" + xp  # коротка форма для токенів
        try:
            return node.xpath(xp)
        except Exception:
            return []

    # CSS шлях
    if isinstance(container, Tag):
        try:
            return list(container.select(selector))
        except Exception:
            return []
    else:
        # перетворимо на bs4 і зробимо відносну вибірку
        frag = BeautifulSoup(html.tostring(container, encoding="unicode"), "lxml")
        root = next((c for c in frag.contents if isinstance(c, Tag)), frag)
        try:
            return list(root.select(selector))
        except Exception:
            return []

def _norm_html(elem, *, get_html: bool, inner_html: bool = False,
               allowed_tags: list[str] | None = None, remove_links: bool = False) -> str:
    """
    Повертає:
      - якщо get_html=True і inner_html=False: outer HTML елемента
      - якщо get_html=True і inner_html=True:  inner HTML елемента (без самого контейнера)
      - якщо get_html=False: plain text
    Працює і для bs4.Tag, і для lxml-елементів.
    """
    # --- BeautifulSoup.Tag ---
    if isinstance(elem, Tag):
        if get_html:
            from bs4 import BeautifulSoup
            frag = BeautifulSoup(str(elem), "html.parser")
            top = next((c for c in frag.contents if isinstance(c, Tag)), None)
            if top is None:
                return ""
            if top.name in ("html", "body"):
                inner_top = next((c for c in top.contents if isinstance(c, Tag)), None)
                if inner_top:
                    top = inner_top

            if remove_links:
                for a in top.find_all("a"):
                    a.unwrap()

            if allowed_tags:
                allow = set(allowed_tags)
                for t in list(top.find_all(True)):
                    if t is top:
                        continue
                    if t.name not in allow:
                        t.unwrap()

            if inner_html:
                # Внутрішній HTML (вміст без контейнера)
                return "".join(str(c) for c in top.contents).strip()

            # Зовнішній HTML (разом із контейнером)
            return top.decode().strip()

        return elem.get_text(" ", strip=True)

    # --- lxml елементи ---
    if get_html:
        from lxml import etree, html
        clone = html.fromstring(etree.tostring(elem, encoding="unicode"))

        if remove_links:
            for a in clone.xpath(".//a"):
                a.drop_tag()

        if allowed_tags:
            allow = set(allowed_tags)
            for e in list(clone.iter()):
                if isinstance(e.tag, str) and e is not clone and e.tag not in allow:
                    e.drop_tag()

        if inner_html:
            # Внутрішній HTML: текст + дочірні вузли (із tail)
            parts: list[str] = []
            if clone.text:
                parts.append(clone.text)
            for child in clone:
                parts.append(etree.tostring(child, encoding="unicode", with_tail=False))
                if child.tail:
                    parts.append(child.tail)
            return "".join(parts).strip()

        # Зовнішній HTML
        return etree.tostring(clone, encoding="unicode", with_tail=False).strip()

    return (elem.text_content() if hasattr(elem, "text_content") else str(elem)).strip()


def _apply_text_ops(val: str, *, regex: str | None, delete_text: str | None, find_text: str | None, replace_text: str | None) -> str:
    import re
    s = val or ""
    if regex:
        m = re.findall(regex, s, flags=re.I | re.M | re.S)
        s = " ".join(m) if m else ""
    if delete_text:
        s = s.replace(delete_text, "")
    if find_text is not None and replace_text is not None:
        s = s.replace(find_text, replace_text)
    return s.strip()
