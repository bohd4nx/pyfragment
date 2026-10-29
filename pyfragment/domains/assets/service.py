from __future__ import annotations

import logging

from pyfragment.constants import FRAGMENT_BASE_URL
from pyfragment.domains.assets.models import MyGiftsResult, MyNumbersResult, MyUsernamesResult
from pyfragment.domains.base import BaseService, operation
from pyfragment.domains.marketplace.parser import parse_auction_rows, parse_gift_items

logger = logging.getLogger(__name__)

_MY_USERNAMES_URL = f"{FRAGMENT_BASE_URL}/my/usernames"
_MY_NUMBERS_URL = f"{FRAGMENT_BASE_URL}/my/numbers"
_MY_GIFTS_URL = f"{FRAGMENT_BASE_URL}/my/gifts"


class AssetsService(BaseService):
    async def get_my_usernames(self) -> MyUsernamesResult:
        with operation(logger, "list owned usernames"):
            html = await self._client._transport.fetch_page(_MY_USERNAMES_URL)
            items, _ = parse_auction_rows(html)
            return MyUsernamesResult(items=items)

    async def get_my_numbers(self) -> MyNumbersResult:
        with operation(logger, "list owned numbers"):
            html = await self._client._transport.fetch_page(_MY_NUMBERS_URL)
            items, _ = parse_auction_rows(html)
            return MyNumbersResult(items=items)

    async def get_my_gifts(self) -> MyGiftsResult:
        with operation(logger, "list owned gifts"):
            html = await self._client._transport.fetch_page(_MY_GIFTS_URL)
            items, _ = parse_gift_items(html)
            return MyGiftsResult(items=items)
