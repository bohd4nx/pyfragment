from __future__ import annotations

import re

from pyfragment.domains.marketplace.models import AuctionItem

# Row listings (usernames, numbers): one <tr class="tm-row-selectable"> per item.
_ROW_RE = re.compile(r'<tr\b[^>]*class="[^"]*tm-row-selectable[^"]*"[^>]*>(.*?)</tr>', re.DOTALL)
_ROW_HREF_RE = re.compile(r'href="/((?:username|number|gift)/[^"?]+)')
_ROW_NAME_RE = re.compile(r'class="[^"]*\btm-value\b[^"]*"[^>]*>\s*([^<]+?)\s*<')
_ROW_PRICE_RE = re.compile(r'class="[^"]*\btm-value\b[^"]*\bicon-ton\b[^"]*"[^>]*>\s*([0-9][^<]*?)\s*<')
_ROW_STATUS_RE = re.compile(r'class="[^"]*\btm-value\b[^"]*\btm-status-\w+[^"]*"[^>]*>\s*([^<]+?)\s*<')

# Grid listings (gifts): one <a class="tm-grid-item"> card per item.
_CARD_RE = re.compile(r'(<a\b[^>]*class="[^"]*\btm-grid-item\b[^"]*"[^>]*>.*?</a>)', re.DOTALL)
_CARD_HREF_RE = re.compile(r'href="/(gift/[^?"]+)')
_CARD_NAME_RE = re.compile(r'class="item-name">([^<]+)<')
_CARD_NUMBER_RE = re.compile(r'class="item-num">[^#]*#(\w+)<')
_CARD_PRICE_RE = re.compile(r'class="[^"]*\btm-grid-item-value\b[^"]*\bicon-ton\b[^"]*"[^>]*>\s*([0-9][^<]*?)\s*<')
_CARD_STATUS_RE = re.compile(r'class="[^"]*\btm-grid-item-status\b[^"]*"[^>]*>(.*?)</div>', re.DOTALL)
# Some statuses ("On auction") are split into a short mobile and a full desktop <span>; prefer the full one.
_WIDE_TEXT_RE = re.compile(r'<span class="wide-only">([^<]*)</span>')
_TAG_RE = re.compile(r"<[^>]+>")

_TIME_RE = re.compile(r'<time[^>]+datetime="([^"]+)"')
_NEXT_OFFSET_RE = re.compile(r'data-next-offset="(\d+)"')


def first(pattern: re.Pattern[str], html: str) -> str | None:
    match = pattern.search(html)
    return match.group(1).strip() if match else None


def normalize_price(raw_price: str | None) -> str | None:
    """``"24,740"`` -> ``"24740.00"``; anything that isn't a number is returned as is."""
    if raw_price is None:
        return None
    digits = raw_price.replace(",", "")
    try:
        return f"{float(digits):.2f}"
    except ValueError:
        return digits


def parse_auction_rows(html: str) -> tuple[list[AuctionItem], str | None]:
    """Parse a usernames/numbers listing into items plus the ``offset_id`` of the next page, if any."""
    items: list[AuctionItem] = []
    for row in _ROW_RE.findall(html):
        slug = first(_ROW_HREF_RE, row)
        if slug is None:
            # The "Show more" footer is a row without a link.
            continue
        items.append(
            AuctionItem(
                slug=slug,
                name=first(_ROW_NAME_RE, row) or slug,
                status=first(_ROW_STATUS_RE, row),
                price=normalize_price(first(_ROW_PRICE_RE, row)),
                date=first(_TIME_RE, row),
            )
        )
    return items, first(_NEXT_OFFSET_RE, html)


def card_status(card: str) -> str | None:
    match = _CARD_STATUS_RE.search(card)
    if not match:
        return None
    inner = match.group(1)
    wide = _WIDE_TEXT_RE.search(inner)
    return (wide.group(1) if wide else _TAG_RE.sub("", inner)).strip() or None


def parse_gift_items(html: str) -> tuple[list[AuctionItem], int | None]:
    """Parse a gifts listing into items plus the ``offset`` of the next page, if any."""
    items: list[AuctionItem] = []
    for card in _CARD_RE.findall(html):
        slug = first(_CARD_HREF_RE, card)
        if slug is None:
            continue
        name = first(_CARD_NAME_RE, card) or slug
        number = first(_CARD_NUMBER_RE, card)
        items.append(
            AuctionItem(
                slug=slug,
                name=f"{name} #{number}" if number else name,
                status=card_status(card),
                price=normalize_price(first(_CARD_PRICE_RE, card)),
                date=first(_TIME_RE, card),
            )
        )
    if not items:
        # The list view renders gifts as table rows, like usernames and numbers.
        items, next_offset = parse_auction_rows(html)
        return items, int(next_offset) if next_offset else None
    next_offset = first(_NEXT_OFFSET_RE, html)
    return items, int(next_offset) if next_offset else None
