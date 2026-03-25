"""Unit tests for search_auctions — Fragment marketplace search."""

from unittest.mock import AsyncMock, patch

import pytest

from pyfragment import FragmentClient
from pyfragment.types import AuctionsResult
from tests.shared import FAKE_HASH

FAKE_HTML = """
<tr class="tm-row-selectable">
  <td><a href="/username/coolname" class="table-cell">
    <div class="table-cell-value tm-value">@coolname</div>
    <div class="table-cell-status-thin thin-only tm-status-avail">On auction</div>
  </a></td>
  <td><div class="table-cell-value tm-value icon-before icon-ton">5</div>
    <time datetime="2026-06-01T12:00:00+00:00" data-relative="text">2 days</time>
  </td>
  <td><div class="table-cell-value tm-value tm-status-avail">On auction</div></td>
</tr>
"""


@pytest.mark.asyncio
async def test_search_auctions_basic(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.search_auctions.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch(
            "pyfragment.methods.search_auctions.fragment_request",
            AsyncMock(return_value={"ok": True, "html": FAKE_HTML}),
        ),
    ):
        result = await client.search_auctions("coolname")

    assert isinstance(result, AuctionsResult)
    assert len(result.items) == 1
    assert result.items[0]["slug"] == "username/coolname"
    assert result.items[0]["name"] == "@coolname"
    assert result.next_offset_id is None


@pytest.mark.asyncio
async def test_search_auctions_with_type(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.search_auctions.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch(
            "pyfragment.methods.search_auctions.fragment_request",
            AsyncMock(return_value={"ok": True, "html": FAKE_HTML, "next_offset_id": "offset_99"}),
        ),
    ):
        result = await client.search_auctions("coolname", type="usernames")

    assert isinstance(result, AuctionsResult)
    assert len(result.items) == 1
    assert result.next_offset_id == "offset_99"


@pytest.mark.asyncio
async def test_search_auctions_numbers(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.search_auctions.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch(
            "pyfragment.methods.search_auctions.fragment_request",
            AsyncMock(return_value={"ok": True, "html": FAKE_HTML}),
        ),
    ):
        result = await client.search_auctions("888", type="numbers")

    assert isinstance(result, AuctionsResult)
    assert isinstance(result.items, list)


@pytest.mark.asyncio
async def test_search_auctions_empty_html(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.search_auctions.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch(
            "pyfragment.methods.search_auctions.fragment_request",
            AsyncMock(return_value={"ok": True}),
        ),
    ):
        result = await client.search_auctions("zzz_no_results")

    assert isinstance(result, AuctionsResult)
    assert result.items == []
    assert result.next_offset_id is None


@pytest.mark.asyncio
async def test_search_auctions_with_sort_and_filter(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.search_auctions.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch(
            "pyfragment.methods.search_auctions.fragment_request",
            AsyncMock(return_value={"ok": True, "html": FAKE_HTML}),
        ) as mock_request,
    ):
        result = await client.search_auctions("durov", type="usernames", sort="price_desc", filter="auction")

    assert isinstance(result, AuctionsResult)
    call_data = mock_request.call_args[0][3]
    assert call_data["sort"] == "price_desc"
    assert call_data["filter"] == "auction"
    assert call_data["type"] == "usernames"
    assert call_data["query"] == "durov"


@pytest.mark.asyncio
async def test_search_auctions_with_offset_id(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.search_auctions.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch(
            "pyfragment.methods.search_auctions.fragment_request",
            AsyncMock(return_value={"ok": True, "html": FAKE_HTML}),
        ) as mock_request,
    ):
        result = await client.search_auctions("durov", type="usernames", offset_id="offset_10")

    assert isinstance(result, AuctionsResult)
    call_data = mock_request.call_args[0][3]
    assert call_data["offset_id"] == "offset_10"
    assert call_data["type"] == "usernames"
    assert call_data["query"] == "durov"
