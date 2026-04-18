from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyfragment.types import FragmentAPIError, FragmentError, GiftsResult, UnexpectedError
from pyfragment.types.constants import GIFTS_PAGE
from pyfragment.utils import parse_gift_items

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


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
    """Search the Fragment gifts marketplace.

    Args:
        client: Authenticated :class:`FragmentClient` instance.
        query: Search text. Omit or pass ``""`` to browse without filtering by name.
        collection: Filter by gift collection slug (e.g. ``"artisanbrick"``). Omit for all.
        sort: Sort order — ``"price_desc"``, ``"price_asc"``, ``"listed"``, or
            ``"ending"``. Omit to use Fragment's default ordering.
        filter: Filter results — ``"auction"``, ``"sale"``, ``"sold"``, or ``""``
            (available items). Omit to return all.
        view: Active attribute tab name (e.g. ``"Model"``, ``"Backdrop"``). Omit for default.
        attr: Attribute filters as a mapping of trait name to list of accepted values, e.g.
            ``{"Model": ["Foosball"], "Backdrop": ["Celtic Blue", "Orange"]}``.
            Each key is sent as ``attr[Key]`` with its list of values.
        offset: Integer page offset from a previous :class:`GiftsResult`.
            Pass ``next_offset`` to fetch the next page.

    Returns:
        :class:`GiftsResult` with ``items`` (parsed list of item dicts) and
        ``next_offset`` (``None`` on the last page).

    Raises:
        FragmentAPIError: If the Fragment API returns an error.
        UnexpectedError: For any other unexpected failure.
    """
    data: dict[str, Any] = {"method": "searchAuctions", "type": "gifts", "query": query}
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

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc
