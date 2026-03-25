import re
from typing import Any

# Matches the login code inside a table-cell-value element.
CODE_RE = re.compile(r'class="[^"]*table-cell-value[^"]*"[^>]*>([^<]+)<')
# Counts active session rows in the HTML table.
ROW_RE = re.compile(r"<tr[\s>]")

# Auction table row parsing
ROW_BLOCK_RE = re.compile(r'<tr\b[^>]*class="[^"]*tm-row-selectable[^"]*"[^>]*>(.*?)</tr>', re.DOTALL)
HREF_RE = re.compile(r'href="(/(?:username|number|nft)/([^"]+))"')
VALUE_RE = re.compile(r'class="[^"]*tm-value[^"]*"[^>]*>\s*([^<]+?)\s*<')
PRICE_RE = re.compile(r"icon-before\s+icon-ton[^>]*>\s*([0-9][^<]*?)\s*<")
DATETIME_RE = re.compile(r'<time[^>]+datetime="([^"]+)"[^>]*data-relative="text"[^>]*>')
DATETIME_SHORT_RE = re.compile(r'<time[^>]+datetime="([^"]+)"[^>]*data-relative="short-text"[^>]*>')
# Matches numeric-only values (plain integers, formatted prices like "150,492", phone numbers like "+888 0088 8888")
NUMERIC_RE = re.compile(r"^\+?[\d,. ]+$")

# Gift grid item parsing
GRID_ITEM_RE = re.compile(r'<a\b[^>]*class="[^"]*tm-grid-item[^"]*"[^>]*>(.*?)</a>', re.DOTALL)
GRID_HREF_RE = re.compile(r'href="(/gift/([^?"]+))')
GRID_NAME_RE = re.compile(r'class="item-name">([^<]+)<')
GRID_NUM_RE = re.compile(r'class="item-num">[^#]*#(\w+)<')
GRID_PRICE_RE = re.compile(r'class="[^"]*tm-grid-item-value[^"]*icon-ton[^"]*"[^>]*>\s*([0-9][^<]*?)\s*<')
GRID_STATUS_RE = re.compile(r'class="[^"]*tm-grid-item-status[^"]*"[^>]*>\s*([^<]+?)\s*<')
GRID_DATETIME_RE = re.compile(r'<time[^>]+datetime="([^"]+)"')


def parse_login_code(html: str) -> tuple[str | None, int]:
    """Extract the pending login code and active session count from a Fragment numbers page HTML snippet.

    Args:
        html: Raw HTML string returned by the Fragment API.

    Returns:
        A tuple of ``(code, active_sessions)`` where ``code`` is ``None`` if no
        pending code is present, and ``active_sessions`` is the number of ``<tr>``
        rows found (each row represents one active session).
    """
    match = CODE_RE.search(html)
    code = match.group(1).strip() if match else None
    active_sessions = len(ROW_RE.findall(html))
    return code, active_sessions


def parse_auction_rows(html: str) -> list[dict[str, Any]]:
    """Parse Fragment marketplace HTML into structured item dicts.

    Extracts each ``<tr class="tm-row-selectable">`` and returns a list of dicts
    with the following keys:

    - ``slug`` — URL path segment (e.g. ``"username/durov"``).
    - ``name`` — display value (e.g. ``"@durov"`` or ``"+888..."``)
    - ``status`` — human-readable Fragment label (e.g. ``"On auction"``, ``"For sale"``).
    - ``price`` — price in TON formatted to two decimal places (e.g. ``"7.00"``),
      or ``None`` if not listed.
    - ``date`` — ISO 8601 datetime string: auction end date, sale date, or listing date, or ``None``.

    Returns:
        List of item dicts, one per table row.
    """
    items: list[dict[str, Any]] = []
    for row_match in ROW_BLOCK_RE.finditer(html):
        row = row_match.group(1)

        href_m = HREF_RE.search(row)
        if not href_m:
            continue
        slug = href_m.group(1).lstrip("/")  # e.g. "username/durov"

        # All tm-value spans in the row — first is the display name
        values = [m.group(1).strip() for m in VALUE_RE.finditer(row)]
        name = values[0] if values else slug

        # Status: find the human-readable label from subsequent tm-value spans.
        # Skip usernames (@), numeric-only values (prices like "150,492", phone numbers like "+888 0088 8888").
        status: str | None = None
        for v in values[1:]:
            if v and v not in ("Unknown",) and not v.startswith("@") and not NUMERIC_RE.match(v):
                status = v
                break

        # Price — look for icon-ton pattern, format as two decimal places
        price_m = PRICE_RE.search(row)
        price: str | None = None
        if price_m:
            raw_price = price_m.group(1).strip().replace(",", "")
            try:
                price = f"{float(raw_price):.2f}"
            except ValueError:
                price = raw_price

        # Datetime (ISO 8601) — auction end, sale date, or listing date.
        time_m = DATETIME_RE.search(row) or DATETIME_SHORT_RE.search(row)
        date: str | None = time_m.group(1) if time_m else None

        items.append(
            {
                "slug": slug,
                "name": name,
                "status": status,
                "price": price,
                "date": date,
            }
        )
    return items


def parse_gift_items(html: str) -> tuple[list[dict[str, Any]], int | None]:
    """Parse Fragment gifts grid HTML into structured item dicts.

    Extracts each ``<a class="tm-grid-item">`` block and returns a list of dicts
    with the following keys:

    - ``slug`` — URL path segment (e.g. ``"gift/plushpepe-1821"``).
    - ``name`` — display name with number (e.g. ``"Plush Pepe #1821"``).
    - ``status`` — human-readable Fragment label (e.g. ``"Sold"``, ``"For sale"``).
    - ``price`` — price in TON formatted to two decimal places, or ``None``.
    - ``date`` — ISO 8601 datetime of the sale/listing, or ``None``.

    Returns:
        Tuple of ``(items, next_offset)`` where ``next_offset`` is an integer
        page offset from ``data-next-offset``, or ``None`` on the last page.
    """
    items: list[dict[str, Any]] = []
    for item_match in GRID_ITEM_RE.finditer(html):
        block = item_match.group(0)

        href_m = GRID_HREF_RE.search(block)
        if not href_m:
            continue
        slug = href_m.group(1).lstrip("/")  # e.g. "gift/plushpepe-1821"

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

    # Pagination offset from data-next-offset attribute
    next_offset_m = re.search(r'data-next-offset="(\d+)"', html)
    next_offset = int(next_offset_m.group(1)) if next_offset_m else None

    return items, next_offset
