from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pyfragment.constants.fragment import MY_GIFTS_PAGE, MY_NUMBERS_PAGE, MY_USERNAMES_PAGE
from pyfragment.domains.assets.models import MyGiftsResult, MyNumbersResult, MyUsernamesResult
from pyfragment.domains.base import operation
from pyfragment.domains.marketplace.parser import parse_auction_rows, parse_gift_items

if TYPE_CHECKING:
    from pyfragment.client.base import BaseClient

logger = logging.getLogger(__name__)


async def get_my_usernames(client: BaseClient) -> MyUsernamesResult:
    with operation(logger, "list owned usernames"):
        items, _ = parse_auction_rows(await client._transport.fetch_page(MY_USERNAMES_PAGE))
        return MyUsernamesResult(items=items)


async def get_my_numbers(client: BaseClient) -> MyNumbersResult:
    with operation(logger, "list owned numbers"):
        items, _ = parse_auction_rows(await client._transport.fetch_page(MY_NUMBERS_PAGE))
        return MyNumbersResult(items=items)


async def get_my_gifts(client: BaseClient) -> MyGiftsResult:
    with operation(logger, "list owned gifts"):
        items, _ = parse_gift_items(await client._transport.fetch_page(MY_GIFTS_PAGE))
        return MyGiftsResult(items=items)
