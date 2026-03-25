"""Unit tests for search_gifts — Fragment gifts marketplace search."""

from unittest.mock import AsyncMock, patch

import pytest

from pyfragment import FragmentClient
from pyfragment.types import GiftsResult
from tests.shared import FAKE_HASH

FAKE_GIFTS_HTML = """
<div class="tm-catalog-grid">
  <a href="/gift/plushpepe-1821?collection=all" class="tm-grid-item">
    <div class="tm-grid-item-thumb">
      <img src="https://nft.fragment.com/gift/plushpepe-1821.medium.jpg" class="tm-grid-thumb"/>
    </div>
    <div class="tm-grid-item-content">
      <div class="tm-grid-item-name wide-only">
        <span class="item-name">Plush Pepe</span>
        <span class="item-num">&nbsp;#1821</span>
      </div>
      <div class="tm-grid-item-desc wide-only">
        <time datetime="2026-02-05T14:41:27+00:00" class="short">Feb 5 at 16:41</time>
      </div>
      <div class="tm-grid-item-values">
        <div class="tm-grid-item-value tm-value icon-before icon-ton">88,888</div>
        <div class="tm-grid-item-status tm-status-unavail">Sold</div>
      </div>
    </div>
  </a>
  <a href="/gift/swisswatch-7799?collection=all" class="tm-grid-item">
    <div class="tm-grid-item-content">
      <div class="tm-grid-item-name wide-only">
        <span class="item-name">Swiss Watch</span>
        <span class="item-num">&nbsp;#7799</span>
      </div>
      <div class="tm-grid-item-desc wide-only">
        <time datetime="2026-01-10T04:52:59+00:00" class="short">Jan 10 at 06:52</time>
      </div>
      <div class="tm-grid-item-values">
        <div class="tm-grid-item-value tm-value icon-before icon-ton">13,588</div>
        <div class="tm-grid-item-status tm-status-unavail">Sold</div>
      </div>
    </div>
  </a>
  <a class="tm-catalog-grid-more js-load-more" data-next-offset="60">Show more</a>
</div>
"""


# search_gifts mocked tests


@pytest.mark.asyncio
async def test_search_gifts_basic(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.search_gifts.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch(
            "pyfragment.methods.search_gifts.fragment_request",
            AsyncMock(return_value={"ok": True, "html": FAKE_GIFTS_HTML}),
        ),
    ):
        result = await client.search_gifts()

    assert isinstance(result, GiftsResult)
    assert len(result.items) == 2
    assert result.items[0]["slug"] == "gift/plushpepe-1821"
    assert result.items[0]["name"] == "Plush Pepe #1821"
    assert result.items[0]["status"] == "Sold"
    assert result.items[0]["price"] == "88888.00"
    assert result.items[0]["date"] == "2026-02-05T14:41:27+00:00"
    assert result.items[1]["slug"] == "gift/swisswatch-7799"
    assert result.items[1]["price"] == "13588.00"
    assert result.next_offset == 60


@pytest.mark.asyncio
async def test_search_gifts_empty(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.search_gifts.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch(
            "pyfragment.methods.search_gifts.fragment_request",
            AsyncMock(return_value={"ok": True}),
        ),
    ):
        result = await client.search_gifts(query="zzz_no_results")

    assert isinstance(result, GiftsResult)
    assert result.items == []
    assert result.next_offset is None


@pytest.mark.asyncio
async def test_search_gifts_with_collection_and_sort(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.search_gifts.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch(
            "pyfragment.methods.search_gifts.fragment_request",
            AsyncMock(return_value={"ok": True, "html": FAKE_GIFTS_HTML}),
        ) as mock_request,
    ):
        result = await client.search_gifts(collection="plushpepe", sort="price_desc", filter="sold")

    assert isinstance(result, GiftsResult)
    call_data = mock_request.call_args[0][3]
    assert call_data["collection"] == "plushpepe"
    assert call_data["sort"] == "price_desc"
    assert call_data["filter"] == "sold"
    assert call_data["type"] == "gifts"
    assert call_data["method"] == "searchAuctions"


@pytest.mark.asyncio
async def test_search_gifts_with_offset(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.search_gifts.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch(
            "pyfragment.methods.search_gifts.fragment_request",
            AsyncMock(return_value={"ok": True, "html": FAKE_GIFTS_HTML}),
        ) as mock_request,
    ):
        result = await client.search_gifts(offset=60)

    assert isinstance(result, GiftsResult)
    call_data = mock_request.call_args[0][3]
    assert call_data["offset"] == 60


@pytest.mark.asyncio
async def test_search_gifts_with_view(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.search_gifts.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch(
            "pyfragment.methods.search_gifts.fragment_request",
            AsyncMock(return_value={"ok": True, "html": FAKE_GIFTS_HTML}),
        ) as mock_request,
    ):
        result = await client.search_gifts(collection="artisanbrick", view="Model")

    assert isinstance(result, GiftsResult)
    call_data = mock_request.call_args[0][3]
    assert call_data["view"] == "Model"
    assert call_data["collection"] == "artisanbrick"


@pytest.mark.asyncio
async def test_search_gifts_with_attr(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.search_gifts.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch(
            "pyfragment.methods.search_gifts.fragment_request",
            AsyncMock(return_value={"ok": True, "html": FAKE_GIFTS_HTML}),
        ) as mock_request,
    ):
        result = await client.search_gifts(
            collection="artisanbrick",
            sort="listed",
            filter="auction",
            attr={
                "Model": ["Delicate Wash", "Foosball", "Chocolate"],
                "Backdrop": ["Celtic Blue", "Carrot Juice", "Orange"],
                "Symbol": ["Crystal Ball", "Tetsubin", "Acorn"],
            },
        )

    assert isinstance(result, GiftsResult)
    call_data = mock_request.call_args[0][3]
    assert call_data["attr[Model]"] == ["Delicate Wash", "Foosball", "Chocolate"]
    assert call_data["attr[Backdrop]"] == ["Celtic Blue", "Carrot Juice", "Orange"]
    assert call_data["attr[Symbol]"] == ["Crystal Ball", "Tetsubin", "Acorn"]
    assert call_data["collection"] == "artisanbrick"
    assert call_data["sort"] == "listed"
    assert call_data["filter"] == "auction"
    assert call_data["type"] == "gifts"


@pytest.mark.asyncio
async def test_search_gifts_attr_not_in_data_when_none(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.search_gifts.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch(
            "pyfragment.methods.search_gifts.fragment_request",
            AsyncMock(return_value={"ok": True, "html": FAKE_GIFTS_HTML}),
        ) as mock_request,
    ):
        result = await client.search_gifts()

    assert isinstance(result, GiftsResult)
    call_data = mock_request.call_args[0][3]
    assert "view" not in call_data
    assert not any(k.startswith("attr[") for k in call_data)
