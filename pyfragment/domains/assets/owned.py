from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pyfragment.constants.fragment import MY_ASSETS_PAGE
from pyfragment.domains.assets.models import MyGiftsResult, MyNumbersResult, MyUsernamesResult
from pyfragment.domains.base import operation
from pyfragment.domains.marketplace.parser import parse_auction_rows, parse_gift_items
from pyfragment.enums import ApiMethod, AssetType
from pyfragment.utils.errors import raise_for_error

if TYPE_CHECKING:
    from pyfragment.client.base import BaseClient

logger = logging.getLogger(__name__)


async def list_assets(client: BaseClient, kind: AssetType) -> str:
    """The markup of every asset of ``kind``: the assets page loads them page by page through ``getAssetsList``."""
    rows: list[str] = []
    offset: object = 0
    while True:
        result = await client.call(ApiMethod.GET_ASSETS_LIST, {"type": kind, "offset_id": offset}, page_url=MY_ASSETS_PAGE)
        raise_for_error(result)
        rows.extend(str(item.get("html", "")) for item in result.get("items") or [])
        following = result.get("next_offset_id")
        if not following or following == offset:
            return "".join(rows)
        offset = following


async def get_my_usernames(client: BaseClient) -> MyUsernamesResult:
    with operation(logger, "list owned usernames"):
        items, _ = parse_auction_rows(await list_assets(client, AssetType.USERNAMES))
        return MyUsernamesResult(items=items)


async def get_my_numbers(client: BaseClient) -> MyNumbersResult:
    with operation(logger, "list owned numbers"):
        items, _ = parse_auction_rows(await list_assets(client, AssetType.NUMBERS))
        return MyNumbersResult(items=items)


async def get_my_gifts(client: BaseClient) -> MyGiftsResult:
    with operation(logger, "list owned gifts"):
        items, _ = parse_gift_items(await list_assets(client, AssetType.GIFTS))
        return MyGiftsResult(items=items)
