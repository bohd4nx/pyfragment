from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pyfragment.constants.fragment import PREMIUM_HISTORY_PAGE, STARS_HISTORY_PAGE
from pyfragment.domains.base import operation
from pyfragment.domains.history.models import PremiumHistoryEntry, StarsHistoryEntry
from pyfragment.domains.history.parser import parse_history_rows, parse_months, parse_stars

if TYPE_CHECKING:
    from pyfragment.client.base import BaseClient

logger = logging.getLogger(__name__)


def history_url(page: str, newest_first: bool) -> str:
    return page if newest_first else f"{page}?sort=asc"


async def get_stars_history(client: BaseClient, newest_first: bool = True) -> list[StarsHistoryEntry]:
    with operation(logger, "get Stars history"):
        page = await client.fetch_page(history_url(STARS_HISTORY_PAGE, newest_first))
        return [
            StarsHistoryEntry(
                username=row.username, name=row.name, stars=parse_stars(row.quantity), gram=row.gram, date=row.date
            )
            for row in parse_history_rows(page)
        ]


async def get_premium_history(client: BaseClient, newest_first: bool = True) -> list[PremiumHistoryEntry]:
    with operation(logger, "get Premium history"):
        page = await client.fetch_page(history_url(PREMIUM_HISTORY_PAGE, newest_first))
        return [
            PremiumHistoryEntry(
                username=row.username, name=row.name, months=parse_months(row.quantity), gram=row.gram, date=row.date
            )
            for row in parse_history_rows(page)
        ]
