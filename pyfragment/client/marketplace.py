from __future__ import annotations

from collections.abc import Mapping, Sequence

from pyfragment.client.base import BaseClient
from pyfragment.domains.marketplace.models import GiftsResult, NumbersResult, UsernamesResult
from pyfragment.domains.marketplace.search import search_gifts, search_numbers, search_usernames
from pyfragment.enums import AuctionFilter, AuctionSort


class MarketplaceMethods(BaseClient):
    async def search_usernames(
        self,
        query: str = "",
        sort: AuctionSort | str | None = None,
        filter: AuctionFilter | str | None = None,
        offset_id: str | None = None,
    ) -> UsernamesResult:
        """Search the Fragment marketplace for Telegram usernames.

        Args:
            query: Search text. Omit or pass ``""`` to browse all.
            sort: An :class:`AuctionSort` or its value: ``"price"`` (default), ``"price_desc"``,
                ``"price_asc"``, ``"listed"``, or ``"ending"``.
            filter: An :class:`AuctionFilter` or its value: ``""`` (available, default), ``"auction"``,
                ``"sale"``, or ``"sold"``.
            offset_id: Pass :attr:`UsernamesResult.next_offset_id` to fetch the next page.

        Returns:
            :class:`UsernamesResult` with ``items`` and ``next_offset_id``.
        """
        return await search_usernames(self, query, sort=sort, filter=filter, offset_id=offset_id)

    async def search_numbers(
        self,
        query: str = "",
        sort: AuctionSort | str | None = None,
        filter: AuctionFilter | str | None = None,
        offset_id: str | None = None,
    ) -> NumbersResult:
        """Search the Fragment marketplace for anonymous Telegram numbers.

        Args:
            query: Search text. Omit or pass ``""`` to browse all.
            sort: An :class:`AuctionSort` or its value: ``"price"`` (default), ``"price_desc"``,
                ``"price_asc"``, ``"listed"``, or ``"ending"``.
            filter: An :class:`AuctionFilter` or its value: ``""`` (available, default), ``"auction"``,
                ``"sale"``, or ``"sold"``.
            offset_id: Pass :attr:`NumbersResult.next_offset_id` to fetch the next page.

        Returns:
            :class:`NumbersResult` with ``items`` and ``next_offset_id``.
        """
        return await search_numbers(self, query, sort=sort, filter=filter, offset_id=offset_id)

    async def search_gifts(
        self,
        query: str = "",
        collection: str | None = None,
        sort: AuctionSort | str | None = None,
        filter: AuctionFilter | str | None = None,
        view: str | None = None,
        attr: Mapping[str, Sequence[str]] | None = None,
        offset: int | None = None,
    ) -> GiftsResult:
        """Search the Fragment gifts marketplace.

        Args:
            query: Search text. Omit or pass ``""`` to browse all.
            collection: Gift collection slug (e.g. ``"artisanbrick"``).
            sort: An :class:`AuctionSort` or its value: ``"price"`` (default), ``"price_desc"``,
                ``"price_asc"``, ``"listed"``, or ``"ending"``.
            filter: An :class:`AuctionFilter` or its value: ``""`` (available, default), ``"auction"``,
                ``"sale"``, or ``"sold"``.
            view: Active attribute tab name (e.g. ``"Model"``).
            attr: Trait filters keyed by :class:`GiftAttribute` name (``Model``, ``Backdrop`` or ``Symbol``,
                any casing) — e.g. ``{"Model": ["Foosball"], "Backdrop": ["Celtic Blue"]}``.
            offset: Pass :attr:`GiftsResult.next_offset` to fetch the next page.

        Returns:
            :class:`GiftsResult` with ``items`` and ``next_offset``.
        """
        return await search_gifts(
            self, query, collection=collection, sort=sort, filter=filter, view=view, attr=attr, offset=offset
        )
