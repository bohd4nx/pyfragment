from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyfragment.types import FragmentAPIError, FragmentError, NumbersResult, UnexpectedError
from pyfragment.types.constants import NUMBERS_PAGE
from pyfragment.utils import parse_auction_rows

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


async def search_numbers(
    client: FragmentClient,
    query: str = "",
    sort: str | None = None,
    filter: str | None = None,
    offset_id: str | None = None,
) -> NumbersResult:
    """Search the Fragment marketplace for anonymous Telegram numbers.

    Args:
        client: Authenticated :class:`FragmentClient` instance.
        query: Search text (e.g. ``"888"``). Omit or pass ``""`` to browse all.
        sort: Sort order — ``"price_desc"``, ``"price_asc"``, ``"listed"``, or
            ``"ending"``. Omit to use Fragment's default ordering.
        filter: Filter results — ``"auction"``, ``"sale"``, ``"sold"``, or ``""``
            (available items). Omit to return all.
        offset_id: Pagination cursor from a previous :class:`NumbersResult`.
            Pass ``next_offset_id`` to fetch the next page.

    Returns:
        :class:`NumbersResult` with ``items`` (parsed list of item dicts) and
        ``next_offset_id`` (``None`` when there are no more pages).

    Raises:
        FragmentAPIError: If the Fragment API returns an error.
        UnexpectedError: For any other unexpected failure.
    """
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

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc
