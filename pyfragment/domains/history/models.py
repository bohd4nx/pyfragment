from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class StarsHistoryEntry:
    """One Stars purchase of the account's history.

    ``username`` is ``None`` when Fragment shows the recipient by ``name`` only (a deleted or hidden account).
    """

    username: str | None
    name: str
    stars: int
    gram: Decimal
    date: datetime


@dataclass(frozen=True)
class PremiumHistoryEntry:
    """One Premium gift of the account's history; ``username`` is ``None`` as in :class:`StarsHistoryEntry`."""

    username: str | None
    name: str
    months: int
    gram: Decimal
    date: datetime
