"""Unit tests for search_numbers — Fragment marketplace number search."""

from unittest.mock import AsyncMock, patch

import pytest

from pyfragment import FragmentClient
from pyfragment.types import NumbersResult
from tests.shared import FAKE_HASH

FAKE_HTML = """
<tr class="tm-row-selectable">
  <td><a href="/number/8880000888" class="table-cell">
    <div class="table-cell-value tm-value">+888 0000 888</div>
    <div class="table-cell-status-thin thin-only tm-status-avail">For sale</div>
  </a></td>
  <td><div class="table-cell-value tm-value icon-before icon-ton">150</div>
    <time datetime="2026-05-15T10:00:00+00:00" data-relative="short-text">May 15</time>
  </td>
  <td><div class="table-cell-value tm-value tm-status-avail">For sale</div></td>
</tr>
"""


# search_numbers mocked tests


@pytest.mark.asyncio
async def test_search_numbers_basic(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.search_numbers.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch(
            "pyfragment.methods.search_numbers.fragment_request",
            AsyncMock(return_value={"ok": True, "html": FAKE_HTML}),
        ),
    ):
        result = await client.search_numbers("888")

    assert isinstance(result, NumbersResult)
    assert len(result.items) == 1
    assert result.items[0]["slug"] == "number/8880000888"
    assert result.items[0]["name"] == "+888 0000 888"
    assert result.items[0]["date"] == "2026-05-15T10:00:00+00:00"
    assert result.next_offset_id is None


@pytest.mark.asyncio
async def test_search_numbers_empty_html(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.search_numbers.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch(
            "pyfragment.methods.search_numbers.fragment_request",
            AsyncMock(return_value={"ok": True}),
        ),
    ):
        result = await client.search_numbers("zzz_no_results")

    assert isinstance(result, NumbersResult)
    assert result.items == []
    assert result.next_offset_id is None


@pytest.mark.asyncio
async def test_search_numbers_with_sort_and_filter(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.search_numbers.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch(
            "pyfragment.methods.search_numbers.fragment_request",
            AsyncMock(return_value={"ok": True, "html": FAKE_HTML}),
        ) as mock_request,
    ):
        result = await client.search_numbers("888", sort="price_asc", filter="sale")

    assert isinstance(result, NumbersResult)
    call_data = mock_request.call_args[0][3]
    assert call_data["type"] == "numbers"
    assert call_data["method"] == "searchAuctions"
    assert call_data["sort"] == "price_asc"
    assert call_data["filter"] == "sale"
    assert call_data["query"] == "888"


@pytest.mark.asyncio
async def test_search_numbers_with_offset_id(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.search_numbers.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch(
            "pyfragment.methods.search_numbers.fragment_request",
            AsyncMock(return_value={"ok": True, "html": FAKE_HTML, "next_offset_id": "offset_50"}),
        ) as mock_request,
    ):
        result = await client.search_numbers("888", offset_id="offset_50")

    assert isinstance(result, NumbersResult)
    assert result.next_offset_id == "offset_50"
    call_data = mock_request.call_args[0][3]
    assert call_data["offset_id"] == "offset_50"


@pytest.mark.asyncio
async def test_search_numbers_default_query(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.search_numbers.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch(
            "pyfragment.methods.search_numbers.fragment_request",
            AsyncMock(return_value={"ok": True, "html": FAKE_HTML}),
        ) as mock_request,
    ):
        result = await client.search_numbers()

    assert isinstance(result, NumbersResult)
    call_data = mock_request.call_args[0][3]
    assert call_data["query"] == ""
    assert call_data["type"] == "numbers"
