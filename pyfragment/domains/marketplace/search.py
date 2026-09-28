from __future__ import annotations

import json
import logging
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any

from pyfragment.core.constants import FRAGMENT_BASE_URL, GIFTS_PAGE, NUMBERS_PAGE
from pyfragment.core.validation import normalize_filter, normalize_gift_attributes, normalize_sort
from pyfragment.domains.base import operation
from pyfragment.domains.marketplace.models import AuctionItem, GiftsResult, NumbersResult, UsernamesResult
from pyfragment.domains.marketplace.parser import parse_auction_rows, parse_gift_items
from pyfragment.enums import ApiMethod, AuctionFilter, AuctionSort, MarketplaceType
from pyfragment.exceptions import FragmentAPIError
from pyfragment.schemas import error_text

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


logger = logging.getLogger(__name__)


def _listing_query(kind: MarketplaceType, query: str, sort: str | None, filter: str | None, **extra: Any) -> dict[str, Any]:
    data: dict[str, Any] = {"type": kind, "query": query}
    if (sort_order := normalize_sort(sort)) is not None:
        data["sort"] = sort_order
    if (listing_filter := normalize_filter(filter)) is not None:
        data["filter"] = listing_filter
    data.update({key: value for key, value in extra.items() if value is not None})
    return data


async def _fetch_listing(client: FragmentClient, page_url: str, data: dict[str, Any]) -> str:
    result = await client.call(ApiMethod.SEARCH_AUCTIONS, data, page_url=page_url)
    if error := error_text(result):
        raise FragmentAPIError(error)

    # Paginated (offset) responses come back as {"part": true, "body": ..., "foot": ...}
    # instead of a single "html" field - stitch them together before parsing.
    html = result.get("html")
    if html is None:
        html = (result.get("body") or "") + (result.get("foot") or "")
    return str(html)


async def _search_rows(
    client: FragmentClient,
    kind: MarketplaceType,
    page_url: str,
    query: str,
    sort: str | None,
    filter: str | None,
    offset_id: str | None,
) -> tuple[list[AuctionItem], str | None]:
    """Run a usernames/numbers search and parse its rows."""
    data = _listing_query(kind, query, sort, filter, offset_id=offset_id)
    with operation(
        logger, "search %s (query='%s', sort='%s', filter='%s', offset_id='%s')", kind, query, sort, filter, offset_id
    ):
        return parse_auction_rows(await _fetch_listing(client, page_url, data))


async def search_usernames(
    client: FragmentClient,
    query: str = "",
    sort: AuctionSort | str | None = None,
    filter: AuctionFilter | str | None = None,
    offset_id: str | None = None,
) -> UsernamesResult:
    items, next_offset_id = await _search_rows(
        client, MarketplaceType.USERNAMES, FRAGMENT_BASE_URL, query, sort, filter, offset_id
    )
    return UsernamesResult(items=items, next_offset_id=next_offset_id)


async def search_numbers(
    client: FragmentClient,
    query: str = "",
    sort: AuctionSort | str | None = None,
    filter: AuctionFilter | str | None = None,
    offset_id: str | None = None,
) -> NumbersResult:
    items, next_offset_id = await _search_rows(client, MarketplaceType.NUMBERS, NUMBERS_PAGE, query, sort, filter, offset_id)
    return NumbersResult(items=items, next_offset_id=next_offset_id)


async def search_gifts(
    client: FragmentClient,
    query: str = "",
    collection: str | None = None,
    sort: AuctionSort | str | None = None,
    filter: AuctionFilter | str | None = None,
    view: str | None = None,
    attr: Mapping[str, Sequence[str]] | None = None,
    offset: int | None = None,
) -> GiftsResult:
    data = _listing_query(MarketplaceType.GIFTS, query, sort, filter, collection=collection, view=view, offset_id=offset)
    for trait, values in normalize_gift_attributes(attr).items():
        data[f"attr[{trait}]"] = json.dumps(values)

    with operation(
        logger,
        "search gifts (query='%s', collection='%s', sort='%s', filter='%s', view='%s', offset='%s')",
        query,
        collection,
        sort,
        filter,
        view,
        offset,
    ):
        html = await _fetch_listing(client, GIFTS_PAGE, data)
        items, next_offset = parse_gift_items(html)
        return GiftsResult(items=items, next_offset=next_offset)
