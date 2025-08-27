# app/services/scraper.py
from __future__ import annotations

import time
from typing import Any, Dict, List, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag
from lxml import html as lxml_html


DEFAULT_UA = "PriceCompProBot/1.0 (+https://example.local)"


# ---------------------------
# Helpers
# ---------------------------

def _fetch(url: str, ua: str | None = None, delay: float = 0.0) -> str:
    """
    Завантажує HTML сторінки й повертає text (str).
    """
    headers = {"User-Agent": ua or DEFAULT_UA}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    if delay and delay > 0:
        time.sleep(delay)
    # requests.text вже декодований у str згідно з кодуванням сторінки
    return resp.text or ""


def _uniq_keep_order(items: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for it in items:
        if it not in seen:
            seen.add(it)
            out.append(it)
    return out


def _soup_select(soup: BeautifulSoup, selector: str) -> List[Tag]:
    """
    CSS-вибірка через BeautifulSoup (soup.select).
    Повертає список тегів (bs4.Tag).
    """
    try:
        return list(soup.select(selector))
    except Exception:
        return []


def _lxml_xpath(doc: Any, xpath: str) -> List[Any]:
    """
    XPATH-вибірка через lxml.
    """
    try:
        return list(doc.xpath(xpath))
    except Exception:
        return []


def _ensure_lxml_doc(soup: BeautifulSoup) -> Any:
    """
    Перетворення soup → lxml.html.HtmlElement для xpath.
    """
    return lxml_html.fromstring(str(soup))


def _extract_links_from_nodes(nodes: List[Any], base_url: str) -> List[str]:
    """
    Пробує витягнути href з вузлів (і bs4.Tag, і lxml Element),
    або з <a> всередині.
    """
    links: List[str] = []

    for node in nodes:
        # Випадок BeautifulSoup Tag
        if isinstance(node, Tag):
            # сам <a>
            if node.name == "a" and node.has_attr("href"):
                links.append(urljoin(base_url, node.get("href", "").strip()))
                continue
            # інші теги: спробуємо знайти <a> всередині
            for a in node.find_all("a", href=True):
                links.append(urljoin(base_url, a.get("href", "").strip()))
            continue

        # Випадок lxml Element
        try:
            tag = getattr(node, "tag", None)
            if tag is not None:
                # сам <a>
                href = node.get("href")
                if (getattr(node, "tag", "").lower() == "a") and href:
                    links.append(urljoin(base_url, href.strip()))
                    continue
                # пошук <a> всередині
                for a in node.xpath(".//a[@href]"):
                    href2 = a.get("href")
                    if href2:
                        links.append(urljoin(base_url, href2.strip()))
                    # продовжуємо перебір
                continue
        except Exception:
            # якщо це не lxml-елемент або щось пішло не так — пропускаємо
            pass

    return _uniq_keep_order([u for u in links if u])


def _count_items(nodes: List[Any]) -> int:
    """
    Повертає кількість знайдених елементів для 'product_item'.
    """
    return len(nodes)


# ---------------------------
# Public: preview
# ---------------------------

def preview_block(url: str, rules: Dict[str, Any], ua: str | None = None, delay: float = 0.0) -> Dict[str, Any]:
    """
    Мінімальна перевірка для вкладки «Навігація / Категорія».
    На вхід очікується підблок rules['navigation'] або вже вирізаний словник:
      {
        "category_links": [{"selector": "...", "type": "css|xpath"}, ...],
        "pagination":     [{"selector": "...", "type": "css|xpath"}, ...],
        "product_links":  [{"selector": "...", "type": "css|xpath"}, ...],
        "product_item":   {"selector": "...", "type": "css|xpath"}
      }

    Повертає:
      {
        "items": [
          {
            "categories": [...],
            "pagination": [...],
            "product_links": [...],
            "product_items": <int>
          }
        ],
        "html": "<перші_кілька_тисяч_символів_HTML>"
      }
    """
    html_text = _fetch(url, ua=ua, delay=delay)
    soup = BeautifulSoup(html_text, "lxml")
    ldoc = _ensure_lxml_doc(soup)  # для xpath, якщо буде потрібно

    # Дістанемо підключі без падінь
    nav = rules or {}
    cat_cfg: List[Dict[str, str]] = list(nav.get("category_links") or [])
    pag_cfg: List[Dict[str, str]] = list(nav.get("pagination") or [])
    prod_cfg: List[Dict[str, str]] = list(nav.get("product_links") or [])
    item_cfg: Dict[str, str] | None = nav.get("product_item") or None

    # --- 1) Посилання на категорії
    cat_links: List[str] = []
    for cfg in cat_cfg:
        sel = (cfg.get("selector") or "").strip()
        typ = (cfg.get("type") or ("xpath" if cfg.get("is_xpath") else "css")).lower()
        if not sel:
            continue

        if typ == "css":
            nodes = _soup_select(soup, sel)
        else:
            nodes = _lxml_xpath(ldoc, sel)

        cat_links.extend(_extract_links_from_nodes(nodes, url))

    cat_links = _uniq_keep_order(cat_links)

    # --- 2) Пагінація
    pag_links: List[str] = []
    for cfg in pag_cfg:
        sel = (cfg.get("selector") or "").strip()
        typ = (cfg.get("type") or ("xpath" if cfg.get("is_xpath") else "css")).lower()
        if not sel:
            continue

        if typ == "css":
            nodes = _soup_select(soup, sel)
        else:
            nodes = _lxml_xpath(ldoc, sel)

        pag_links.extend(_extract_links_from_nodes(nodes, url))

    pag_links = _uniq_keep_order(pag_links)

    # --- 3) Лінки товарів
    prod_links: List[str] = []
    for cfg in prod_cfg:
        sel = (cfg.get("selector") or "").strip()
        typ = (cfg.get("type") or ("xpath" if cfg.get("is_xpath") else "css")).lower()
        if not sel:
            continue

        if typ == "css":
            nodes = _soup_select(soup, sel)
        else:
            nodes = _lxml_xpath(ldoc, sel)

        prod_links.extend(_extract_links_from_nodes(nodes, url))

    prod_links = _uniq_keep_order(prod_links)

    # --- 4) Підрахунок "тег товарів" (для режиму «Категорії»)
    product_items_count = 0
    if item_cfg and (item_cfg.get("selector") or "").strip():
        sel = (item_cfg.get("selector") or "").strip()
        typ = (item_cfg.get("type") or ("xpath" if item_cfg.get("is_xpath") else "css")).lower()
        if typ == "css":
            nodes = _soup_select(soup, sel)
        else:
            nodes = _lxml_xpath(ldoc, sel)
        product_items_count = _count_items(nodes)

    # обмежимо HTML для прев’ю, щоб не роздувати відповідь
    html_preview = html_text[:20000]

    return {
        "items": [{
            "categories": cat_links,
            "pagination": pag_links,
            "product_links": prod_links,
            "product_items": product_items_count,
        }],
        "html": html_preview,
    }
