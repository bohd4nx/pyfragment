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
    - ``ends_at`` — ISO 8601 datetime string of auction end, or ``None``.

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

        # Auction end datetime (ISO 8601)
        time_m = DATETIME_RE.search(row) or DATETIME_SHORT_RE.search(row)
        ends_at: str | None = time_m.group(1) if time_m else None

        items.append(
            {
                "slug": slug,
                "name": name,
                "status": status,
                "price": price,
                "ends_at": ends_at,
            }
        )
    return items
