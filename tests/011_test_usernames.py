"""Verify username search parsing and query forwarding."""

from unittest.mock import AsyncMock, patch

import pytest

from pyfragment import FragmentClient, UsernamesResult
from pyfragment.enums import MarketplaceType

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


# search_usernames result parsing tests


@pytest.mark.asyncio
async def test_search_usernames_basic(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(return_value={"ok": True, "html": FAKE_HTML})):
        result = await client.search_usernames("coolname")

    assert isinstance(result, UsernamesResult)
    assert len(result.items) == 1
    assert result.items[0]["slug"] == "username/coolname"
    assert result.items[0]["name"] == "@coolname"
    assert result.items[0]["date"] == "2026-06-01T12:00:00+00:00"
    assert result.next_offset_id is None


@pytest.mark.asyncio
async def test_search_usernames_sold_row_date_without_data_relative(client: FragmentClient) -> None:
    # Sold/plain listings render a bare <time> with no data-relative attribute.
    sold_html = """
    <tr class="tm-row-selectable">
      <td><a href="/username/monk" class="table-cell">
        <div class="table-cell-value tm-value">@monk</div>
        <div class="table-cell-status-thin thin-only tm-status-unavail">Sold</div>
      </a></td>
      <td><div class="table-cell-value tm-value icon-before icon-ton">5,050</div></td>
      <td><a class="table-cell">
        <div class="table-cell-value tm-value tm-status-unavail">Sold</div>
        <time datetime="2024-03-11T18:23:29+00:00">11 Mar 2024 at 21:23</time>
      </a></td>
    </tr>
    """
    with patch.object(client, "call", AsyncMock(return_value={"ok": True, "html": sold_html})):
        result = await client.search_usernames("monk", filter="sold")

    assert result.items[0]["date"] == "2024-03-11T18:23:29+00:00"


@pytest.mark.asyncio
async def test_search_usernames_empty_html(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(return_value={"ok": True})):
        result = await client.search_usernames("zzz_no_results")

    assert isinstance(result, UsernamesResult)
    assert result.items == []
    assert result.next_offset_id is None


# search_usernames parameter forwarding tests


@pytest.mark.asyncio
async def test_search_usernames_with_sort_and_filter(client: FragmentClient) -> None:
    mock_call = AsyncMock(return_value={"ok": True, "html": FAKE_HTML})
    with patch.object(client, "call", mock_call):
        result = await client.search_usernames("durov", sort="price_desc", filter="auction")

    assert isinstance(result, UsernamesResult)
    call_data = mock_call.call_args[0][1]
    assert call_data["type"] == MarketplaceType.USERNAMES
    assert call_data["sort"] == "price_desc"
    assert call_data["filter"] == "auction"
    assert call_data["query"] == "durov"


@pytest.mark.asyncio
async def test_search_usernames_with_offset_id(client: FragmentClient) -> None:
    html_with_next_page = FAKE_HTML + '<a class="js-load-more" data-next-offset="500">Show more</a>'
    mock_call = AsyncMock(return_value={"ok": True, "html": html_with_next_page})
    with patch.object(client, "call", mock_call):
        result = await client.search_usernames("durov", offset_id="offset_10")

    assert isinstance(result, UsernamesResult)
    assert result.next_offset_id == "500"
    call_data = mock_call.call_args[0][1]
    assert call_data["offset_id"] == "offset_10"


@pytest.mark.asyncio
async def test_search_usernames_paginated_response_shape(client: FragmentClient) -> None:
    # Fragment answers offset_id requests with {"part": true, "body": ..., "foot": ...}
    # instead of a single "html" field.
    foot = '<a class="js-load-more" data-next-offset="500">Show more</a>'
    with patch.object(client, "call", AsyncMock(return_value={"ok": True, "part": True, "body": FAKE_HTML, "foot": foot})):
        result = await client.search_usernames("durov", offset_id="offset_10")

    assert isinstance(result, UsernamesResult)
    assert len(result.items) == 1
    assert result.next_offset_id == "500"


@pytest.mark.asyncio
async def test_search_usernames_default_query(client: FragmentClient) -> None:
    mock_call = AsyncMock(return_value={"ok": True, "html": FAKE_HTML})
    with patch.object(client, "call", mock_call):
        result = await client.search_usernames()

    assert isinstance(result, UsernamesResult)
    call_data = mock_call.call_args[0][1]
    assert call_data["query"] == ""
    assert call_data["type"] == MarketplaceType.USERNAMES
