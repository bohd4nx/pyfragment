from __future__ import annotations

from typing import TYPE_CHECKING

from pyfragment.domains.base import BaseService
from pyfragment.domains.marketplace.search import search_gifts, search_numbers, search_usernames
from pyfragment.domains.marketplace.models import GiftsResult, NumbersResult, UsernamesResult

if TYPE_CHECKING:
    pass


class MarketplaceService(BaseService):
    async def search_usernames(
        self,
        query: str = "",
        sort: str | None = None,
        filter: str | None = None,
        offset_id: str | None = None,
    ) -> UsernamesResult:
        return await search_usernames(self._client, query, sort=sort, filter=filter, offset_id=offset_id)

    async def search_numbers(
        self,
        query: str = "",
        sort: str | None = None,
        filter: str | None = None,
        offset_id: str | None = None,
    ) -> NumbersResult:
        return await search_numbers(self._client, query, sort=sort, filter=filter, offset_id=offset_id)

    async def search_gifts(
        self,
        query: str = "",
        collection: str | None = None,
        sort: str | None = None,
        filter: str | None = None,
        view: str | None = None,
        attr: dict[str, list[str]] | None = None,
        offset: int | None = None,
    ) -> GiftsResult:
        return await search_gifts(
            self._client, query, collection=collection, sort=sort, filter=filter, view=view, attr=attr, offset=offset
        )
