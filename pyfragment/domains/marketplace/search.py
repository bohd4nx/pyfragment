from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from pyfragment.core.constants import FRAGMENT_BASE_URL, GIFTS_PAGE, NUMBERS_PAGE
from pyfragment.domains.marketplace.parser import parse_auction_rows, parse_gift_items
from pyfragment.exceptions import FragmentAPIError, FragmentError, UnexpectedError
from pyfragment.models.marketplace import GiftsResult, NumbersResult, UsernamesResult

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


logger = logging.getLogger(__name__)


async def search_usernames(
    client: FragmentClient,
    query: str = "",
    sort: str | None = None,
    filter: str | None = None,
    offset_id: str | None = None,
) -> UsernamesResult:
    data: dict[str, Any] = {"type": "usernames", "query": query}
    if sort is not None:
        data["sort"] = sort
    if filter is not None:
        data["filter"] = filter
    if offset_id is not None:
        data["offset_id"] = offset_id

    try:
        result = await client.call("searchAuctions", data, page_url=FRAGMENT_BASE_URL)
        if result.get("error"):
            raise FragmentAPIError(result["error"])

        items = parse_auction_rows(result.get("html") or "")
        raw_noi = result.get("next_offset_id")
        next_offset_id = str(raw_noi) if raw_noi else None
        return UsernamesResult(items=items, next_offset_id=next_offset_id)

    except FragmentError as exc:
        logger.error(
            "Failed to search usernames (query='%s', sort='%s', filter='%s', offset_id='%s'): %s",
            query,
            sort,
            filter,
            offset_id,
            exc,
            exc_info=True,
        )
        raise
    except Exception as exc:
        logger.exception("Failed to search usernames for query '%s' due to an unexpected error", query)
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc


async def search_numbers(
    client: FragmentClient,
    query: str = "",
    sort: str | None = None,
    filter: str | None = None,
    offset_id: str | None = None,
) -> NumbersResult:
    data: dict[str, Any] = {"type": "numbers", "query": query}
    if sort is not None:
        data["sort"] = sort
    if filter is not None:
        data["filter"] = filter
    if offset_id is not None:
        data["offset_id"] = offset_id

    try:
        result = await client.call("searchAuctions", data, page_url=NUMBERS_PAGE)
        if result.get("error"):
            raise FragmentAPIError(result["error"])

        items = parse_auction_rows(result.get("html") or "")
        raw_noi = result.get("next_offset_id")
        next_offset_id = str(raw_noi) if raw_noi else None
        return NumbersResult(items=items, next_offset_id=next_offset_id)

    except FragmentError as exc:
        logger.error(
            "Failed to search numbers (query='%s', sort='%s', filter='%s', offset_id='%s'): %s",
            query,
            sort,
            filter,
            offset_id,
            exc,
            exc_info=True,
        )
        raise
    except Exception as exc:
        logger.exception("Failed to search numbers for query '%s' due to an unexpected error", query)
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc


async def search_gifts(
    client: FragmentClient,
    query: str = "",
    collection: str | None = None,
    sort: str | None = None,
    filter: str | None = None,
    view: str | None = None,
    attr: dict[str, list[str]] | None = None,
    offset: int | None = None,
) -> GiftsResult:
    data: dict[str, Any] = {"type": "gifts", "query": query}
    if collection is not None:
        data["collection"] = collection
    if sort is not None:
        data["sort"] = sort
    if filter is not None:
        data["filter"] = filter
    if view is not None:
        data["view"] = view
    if attr is not None:
        for trait, values in attr.items():
            data[f"attr[{trait}]"] = values
    if offset is not None:
        data["offset"] = offset

    try:
        result = await client.call("searchAuctions", data, page_url=GIFTS_PAGE)
        if result.get("error"):
            raise FragmentAPIError(result["error"])

        items, next_offset = parse_gift_items(result.get("html") or "")
        return GiftsResult(items=items, next_offset=next_offset)

    except FragmentError as exc:
        logger.error(
            "Failed to search gifts (query='%s', collection='%s', sort='%s', filter='%s', view='%s', offset='%s'): %s",
            query,
            collection,
            sort,
            filter,
            view,
            offset,
            exc,
            exc_info=True,
        )
        raise
    except Exception as exc:
        logger.exception("Failed to search gifts for query '%s' due to an unexpected error", query)
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc
