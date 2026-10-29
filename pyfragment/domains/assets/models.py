from __future__ import annotations

from dataclasses import dataclass

from pyfragment.domains.marketplace.models import AuctionItem


@dataclass
class MyUsernamesResult:
    """Telegram usernames owned by the authenticated account."""

    items: list[AuctionItem]

    def __repr__(self) -> str:
        return f"MyUsernamesResult(items={self.items!r})"


@dataclass
class MyNumbersResult:
    """Anonymous phone numbers owned by the authenticated account."""

    items: list[AuctionItem]

    def __repr__(self) -> str:
        return f"MyNumbersResult(items={self.items!r})"


@dataclass
class MyGiftsResult:
    """Telegram gifts owned by the authenticated account."""

    items: list[AuctionItem]

    def __repr__(self) -> str:
        return f"MyGiftsResult(items={self.items!r})"
