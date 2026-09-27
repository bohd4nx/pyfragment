from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict


class AuctionItem(TypedDict):
    """One marketplace listing. ``slug`` is the Fragment path (e.g. ``username/durov``); ``price`` is in GRAM."""

    slug: str
    name: str
    status: str | None
    price: str | None
    date: str | None


@dataclass
class UsernamesResult:
    items: list[AuctionItem]
    next_offset_id: str | None

    def __repr__(self) -> str:
        return f"UsernamesResult(items={len(self.items)}, next_offset_id={self.next_offset_id!r})"


@dataclass
class NumbersResult:
    items: list[AuctionItem]
    next_offset_id: str | None

    def __repr__(self) -> str:
        return f"NumbersResult(items={len(self.items)}, next_offset_id={self.next_offset_id!r})"


@dataclass
class GiftsResult:
    items: list[AuctionItem]
    next_offset: int | None

    def __repr__(self) -> str:
        return f"GiftsResult(items={len(self.items)}, next_offset={self.next_offset!r})"
