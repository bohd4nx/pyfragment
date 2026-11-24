from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from pyfragment.domains.purchases.parser import parse_gram
from pyfragment.exceptions import ParseError
from pyfragment.utils.money import parse_amount

_ROW_RE = re.compile(r"<tr>(.*?)</tr>", re.DOTALL)
_USERNAME_RE = re.compile(r'<a href="https://t\.me/([^"/]+)"')
_NAME_RE = re.compile(r'class="tm-inline-nowrap[^"]*"[^>]*>([^<]+)<')
_GRAM_RE = re.compile(r'icon-ton">([\d,]*)(?:<span class="mini-frac">(\.\d+)</span>)?')
_DATE_RE = re.compile(r'<time datetime="([^"]+)"')
_QUANTITY_RE = re.compile(r'<div class="(?:table-cell-value tm-value tm-nowrap|tm-nowrap)">([^<]+)</div>')
_DURATION_RE = re.compile(r"(\d+) (month|year)s?")


@dataclass(frozen=True)
class HistoryRow:
    username: str | None  # None when Fragment shows only a name (deleted or hidden account)
    name: str
    quantity: str  # the "Stars" or "Duration" cell, as rendered
    gram: Decimal
    date: datetime


def parse_history_rows(page: str) -> list[HistoryRow]:
    """The rows of a history table. A row that lacks a cell raises instead of silently dropping a purchase."""
    rows = []
    for body in _ROW_RE.findall(page):
        if "<th" in body:
            continue
        username = _USERNAME_RE.search(body)
        name = _NAME_RE.search(body)
        quantity = _QUANTITY_RE.search(body)
        gram = _GRAM_RE.search(body)
        date = _DATE_RE.search(body)
        if not (name and quantity and gram and date):
            raise ParseError(ParseError.UNPARSEABLE.format(context="history", exc=f"unrecognised row {body.strip()[:80]!r}"))
        rows.append(
            HistoryRow(
                username=username.group(1) if username else None,
                name=html.unescape(name.group(1)).strip(),
                quantity=quantity.group(1).strip(),
                gram=parse_gram(gram.group(1), gram.group(2) or ""),
                date=datetime.fromisoformat(date.group(1)),
            )
        )
    return rows


def parse_stars(quantity: str) -> int:
    amount = parse_amount(quantity)
    if amount is None:
        raise ParseError(ParseError.UNPARSEABLE.format(context="Stars history", exc=f"bad amount {quantity!r}"))
    return int(amount)


def parse_months(quantity: str) -> int:
    """``"6 months"`` -> 6, ``"1 year"`` -> 12."""
    found = _DURATION_RE.fullmatch(quantity)
    if not found:
        raise ParseError(ParseError.UNPARSEABLE.format(context="Premium history", exc=f"bad duration {quantity!r}"))
    return int(found.group(1)) * (12 if found.group(2) == "year" else 1)
