from typing import TYPE_CHECKING, Any

import httpx

from pyfragment.types import FragmentAPIError, FragmentError, UnexpectedError
from pyfragment.types.constants import FRAGMENT_BASE_URL
from pyfragment.types.results import AuctionsResult
from pyfragment.utils import fragment_request, get_fragment_hash, make_headers, parse_auction_rows

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient

HEADERS: dict[str, str] = make_headers(FRAGMENT_BASE_URL)


async def search_auctions(
    client: "FragmentClient",
    query: str,
    type: str | None = None,
    sort: str | None = None,
    filter: str | None = None,
    offset_id: str | None = None,
) -> AuctionsResult:
    """Search the Fragment marketplace for usernames, numbers, or collectibles.

    Args:
        client: Authenticated :class:`FragmentClient` instance.
        query: Search text (e.g. ``"durov"`` or ``"888"``).
        type: Narrow results by item type — ``"usernames"``, ``"numbers"``, or
            ``"collectibles"``. Omit to search across all types.
        sort: Sort order — ``"price_desc"``, ``"price_asc"``, ``"listed"``, or
            ``"ending"``. Omit to use Fragment's default ordering.
        filter: Filter results — ``"auction"``, ``"sale"``, ``"sold"``, or ``""``
            (available items). Omit to return all.
        offset_id: Pagination cursor from a previous :class:`AuctionsResult`.
            Pass ``next_offset_id`` to fetch the next page.

    Returns:
        :class:`AuctionsResult` with ``items`` (parsed list of item dicts) and
        ``next_offset_id`` (``None`` when there are no more pages).

    Raises:
        FragmentAPIError: If the Fragment API returns an error.
        UnexpectedError: For any other unexpected failure.
    """
    data: dict[str, Any] = {"method": "searchAuctions", "query": query}
    if type is not None:
        data["type"] = type
    if sort is not None:
        data["sort"] = sort
    if filter is not None:
        data["filter"] = filter
    if offset_id is not None:
        data["offset_id"] = offset_id

    try:
        fragment_hash = await get_fragment_hash(client.cookies, HEADERS, FRAGMENT_BASE_URL, client.timeout)
        async with httpx.AsyncClient(cookies=client.cookies, timeout=client.timeout) as session:
            result = await fragment_request(session, fragment_hash, HEADERS, data)

        if result.get("error"):
            raise FragmentAPIError(result["error"])

        items = parse_auction_rows(result.get("html") or "")
        raw_noi = result.get("next_offset_id")
        next_offset_id = str(raw_noi) if raw_noi else None
        return AuctionsResult(items=items, next_offset_id=next_offset_id)

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc
