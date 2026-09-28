from __future__ import annotations

import re

from pyfragment.domains.marketplace.models import AuctionItem

# Row listings (usernames, numbers): one <tr class="tm-row-selectable"> per item.
ROW_RE = re.compile(r'<tr\b[^>]*class="[^"]*tm-row-selectable[^"]*"[^>]*>(.*?)</tr>', re.DOTALL)
ROW_HREF_RE = re.compile(r'href="/((?:username|number)/[^"]+)"')
ROW_NAME_RE = re.compile(r'class="[^"]*\btm-value\b[^"]*"[^>]*>\s*([^<]+?)\s*<')
ROW_PRICE_RE = re.compile(r'class="[^"]*\btm-value\b[^"]*\bicon-ton\b[^"]*"[^>]*>\s*([0-9][^<]*?)\s*<')
ROW_STATUS_RE = re.compile(r'class="[^"]*\btm-value\b[^"]*\btm-status-\w+[^"]*"[^>]*>\s*([^<]+?)\s*<')

# Grid listings (gifts): one <a class="tm-grid-item"> card per item.
CARD_RE = re.compile(r'(<a\b[^>]*class="[^"]*\btm-grid-item\b[^"]*"[^>]*>.*?</a>)', re.DOTALL)
CARD_HREF_RE = re.compile(r'href="/(gift/[^?"]+)')
CARD_NAME_RE = re.compile(r'class="item-name">([^<]+)<')
CARD_NUMBER_RE = re.compile(r'class="item-num">[^#]*#(\w+)<')
CARD_PRICE_RE = re.compile(r'class="[^"]*\btm-grid-item-value\b[^"]*\bicon-ton\b[^"]*"[^>]*>\s*([0-9][^<]*?)\s*<')
CARD_STATUS_RE = re.compile(r'class="[^"]*\btm-grid-item-status\b[^"]*"[^>]*>(.*?)</div>', re.DOTALL)
# Some statuses ("On auction") are split into a short mobile and a full desktop <span>; prefer the full one.
WIDE_TEXT_RE = re.compile(r'<span class="wide-only">([^<]*)</span>')
TAG_RE = re.compile(r"<[^>]+>")

TIME_RE = re.compile(r'<time[^>]+datetime="([^"]+)"')
NEXT_OFFSET_RE = re.compile(r'data-next-offset="(\d+)"')


def _first(pattern: re.Pattern[str], html: str) -> str | None:
    match = pattern.search(html)
    return match.group(1).strip() if match else None


def _normalize_price(raw_price: str | None) -> str | None:
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
    for row in ROW_RE.findall(html):
        slug = _first(ROW_HREF_RE, row)
        if slug is None:
            # The "Show more" footer is a row without a link.
            continue
        items.append(
            AuctionItem(
                slug=slug,
                name=_first(ROW_NAME_RE, row) or slug,
                status=_first(ROW_STATUS_RE, row),
                price=_normalize_price(_first(ROW_PRICE_RE, row)),
                date=_first(TIME_RE, row),
            )
        )
    return items, _first(NEXT_OFFSET_RE, html)


def _card_status(card: str) -> str | None:
    match = CARD_STATUS_RE.search(card)
    if not match:
        return None
    inner = match.group(1)
    wide = WIDE_TEXT_RE.search(inner)
    return (wide.group(1) if wide else TAG_RE.sub("", inner)).strip() or None


def parse_gift_items(html: str) -> tuple[list[AuctionItem], int | None]:
    """Parse a gifts listing into items plus the ``offset`` of the next page, if any."""
    items: list[AuctionItem] = []
    for card in CARD_RE.findall(html):
        slug = _first(CARD_HREF_RE, card)
        if slug is None:
            continue
        name = _first(CARD_NAME_RE, card) or slug
        number = _first(CARD_NUMBER_RE, card)
        items.append(
            AuctionItem(
                slug=slug,
                name=f"{name} #{number}" if number else name,
                status=_card_status(card),
                price=_normalize_price(_first(CARD_PRICE_RE, card)),
                date=_first(TIME_RE, card),
            )
        )
    next_offset = _first(NEXT_OFFSET_RE, html)
    return items, int(next_offset) if next_offset else None
