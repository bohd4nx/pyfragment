from __future__ import annotations

import re
from typing import Any

ROW_BLOCK_RE = re.compile(r'<tr\b[^>]*class="[^"]*tm-row-selectable[^"]*"[^>]*>(.*?)</tr>', re.DOTALL)
HREF_RE = re.compile(r'href="(/(?:username|number|nft)/([^"]+))"')
VALUE_RE = re.compile(r'class="[^"]*tm-value[^"]*"[^>]*>\s*([^<]+?)\s*<')
PRICE_RE = re.compile(r"icon-before\s+icon-ton[^>]*>\s*([0-9][^<]*?)\s*<")
DATETIME_RE = re.compile(r'<time[^>]+datetime="([^"]+)"[^>]*data-relative="text"[^>]*>')
DATETIME_SHORT_RE = re.compile(r'<time[^>]+datetime="([^"]+)"[^>]*data-relative="short-text"[^>]*>')
NUMERIC_RE = re.compile(r"^\+?[\d,. ]+$")

GRID_ITEM_RE = re.compile(r'<a\b[^>]*class="[^"]*tm-grid-item[^"]*"[^>]*>(.*?)</a>', re.DOTALL)
GRID_HREF_RE = re.compile(r'href="(/gift/([^?"]+))')
GRID_NAME_RE = re.compile(r'class="item-name">([^<]+)<')
GRID_NUM_RE = re.compile(r'class="item-num">[^#]*#(\w+)<')
GRID_PRICE_RE = re.compile(r'class="[^"]*tm-grid-item-value[^"]*icon-ton[^"]*"[^>]*>\s*([0-9][^<]*?)\s*<')
GRID_STATUS_RE = re.compile(r'class="[^"]*tm-grid-item-status[^"]*"[^>]*>\s*([^<]+?)\s*<')
GRID_DATETIME_RE = re.compile(r'<time[^>]+datetime="([^"]+)"')


def parse_auction_rows(html: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for row_match in ROW_BLOCK_RE.finditer(html):
        row = row_match.group(1)

        href_m = HREF_RE.search(row)
        if not href_m:
            continue
        slug = href_m.group(1).lstrip("/")

        values = [m.group(1).strip() for m in VALUE_RE.finditer(row)]
        name = values[0] if values else slug

        status: str | None = None
        for v in values[1:]:
            if v and v not in ("Unknown",) and not v.startswith("@") and not NUMERIC_RE.match(v):
                status = v
                break

        price_m = PRICE_RE.search(row)
        price: str | None = None
        if price_m:
            raw_price = price_m.group(1).strip().replace(",", "")
            try:
                price = f"{float(raw_price):.2f}"
            except ValueError:
                price = raw_price

        time_m = DATETIME_RE.search(row) or DATETIME_SHORT_RE.search(row)
        date: str | None = time_m.group(1) if time_m else None

        items.append({"slug": slug, "name": name, "status": status, "price": price, "date": date})

    return items


def parse_gift_items(html: str) -> tuple[list[dict[str, Any]], int | None]:
    items: list[dict[str, Any]] = []
    for item_match in GRID_ITEM_RE.finditer(html):
        block = item_match.group(0)

        href_m = GRID_HREF_RE.search(block)
        if not href_m:
            continue
        slug = href_m.group(1).lstrip("/")

        name_m = GRID_NAME_RE.search(block)
        num_m = GRID_NUM_RE.search(block)
        item_name = name_m.group(1).strip() if name_m else slug
        item_num = f" #{num_m.group(1)}" if num_m else ""
        name = f"{item_name}{item_num}"

        status_m = GRID_STATUS_RE.search(block)
        status: str | None = status_m.group(1).strip() if status_m else None

        price_m = GRID_PRICE_RE.search(block)
        price: str | None = None
        if price_m:
            raw_price = price_m.group(1).strip().replace(",", "")
            try:
                price = f"{float(raw_price):.2f}"
            except ValueError:
                price = raw_price

        time_m = GRID_DATETIME_RE.search(block)
        date: str | None = time_m.group(1) if time_m else None

        items.append({"slug": slug, "name": name, "status": status, "price": price, "date": date})

    next_offset_m = re.search(r'data-next-offset="(\d+)"', html)
    next_offset = int(next_offset_m.group(1)) if next_offset_m else None

    return items, next_offset
