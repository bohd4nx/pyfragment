"""Tests for get_my_usernames, get_my_numbers, and get_my_gifts."""

from unittest.mock import AsyncMock, patch

import pytest

from pyfragment import FragmentClient, MyGiftsResult, MyNumbersResult, MyUsernamesResult

# Minimal HTML with an API hash (required by fetch_page's session check) and one row.
_HASH_SNIPPET = 'src="\\/api?hash=abc123def456"'

FAKE_USERNAMES_HTML = f"""
<html><head></head><body>
  <script {_HASH_SNIPPET}></script>
  <tr class="tm-row-selectable">
    <td><a href="/username/bohd4nx" class="table-cell">
      <div class="table-cell-value tm-value">@bohd4nx</div>
      <div class="table-cell-status-thin thin-only tm-status-avail">On auction</div>
    </a></td>
    <td><div class="table-cell-value tm-value icon-before icon-ton">100</div>
      <time datetime="2026-01-01T00:00:00+00:00" data-relative="text">1 Jan</time>
    </td>
    <td><div class="table-cell-value tm-value tm-status-avail">On auction</div></td>
  </tr>
</body></html>
"""

FAKE_NUMBERS_HTML = f"""
<html><head></head><body>
  <script {_HASH_SNIPPET}></script>
  <tr class="tm-row-selectable">
    <td><a href="/number/88880123456" class="table-cell">
      <div class="table-cell-value tm-value">+888 012 3456</div>
      <div class="table-cell-status-thin thin-only tm-status-avail">On auction</div>
    </a></td>
    <td><div class="table-cell-value tm-value icon-before icon-ton">50</div>
      <time datetime="2026-03-15T10:00:00+00:00" data-relative="text">Mar 15</time>
    </td>
    <td><div class="table-cell-value tm-value tm-status-avail">On auction</div></td>
  </tr>
</body></html>
"""

FAKE_GIFTS_HTML = f"""
<html><head></head><body>
  <script {_HASH_SNIPPET}></script>
  <div class="tm-section">
    <a href="/nft/foosball-model-123" class="tm-card-nft">
      <div class="tm-card-nft__title">Foosball #123</div>
      <div class="tm-card-nft__status tm-status-avail">For sale</div>
      <div class="tm-card-nft__price icon-before icon-ton">10</div>
    </a>
  </div>
</body></html>
"""

EMPTY_HTML = f"""
<html><head></head><body>
  <script {_HASH_SNIPPET}></script>
  <div class="tm-table-empty">You have no assets yet.</div>
</body></html>
"""


@pytest.mark.asyncio
async def test_get_my_usernames_returns_result(client: FragmentClient) -> None:
    with patch.object(client._transport, "fetch_page", AsyncMock(return_value=FAKE_USERNAMES_HTML)):
        result = await client.get_my_usernames()

    assert isinstance(result, MyUsernamesResult)
    assert len(result.items) == 1
    assert result.items[0]["slug"] == "username/bohd4nx"
    assert result.items[0]["name"] == "@bohd4nx"


@pytest.mark.asyncio
async def test_get_my_usernames_fetches_correct_url(client: FragmentClient) -> None:
    mock_fetch = AsyncMock(return_value=FAKE_USERNAMES_HTML)
    with patch.object(client._transport, "fetch_page", mock_fetch):
        await client.get_my_usernames()

    mock_fetch.assert_called_once()
    url = mock_fetch.call_args[0][0]
    assert url.endswith("/my/usernames")


@pytest.mark.asyncio
async def test_get_my_usernames_empty(client: FragmentClient) -> None:
    with patch.object(client._transport, "fetch_page", AsyncMock(return_value=EMPTY_HTML)):
        result = await client.get_my_usernames()

    assert isinstance(result, MyUsernamesResult)
    assert result.items == []


@pytest.mark.asyncio
async def test_get_my_numbers_returns_result(client: FragmentClient) -> None:
    with patch.object(client._transport, "fetch_page", AsyncMock(return_value=FAKE_NUMBERS_HTML)):
        result = await client.get_my_numbers()

    assert isinstance(result, MyNumbersResult)
    assert len(result.items) == 1
    assert result.items[0]["slug"] == "number/88880123456"


@pytest.mark.asyncio
async def test_get_my_numbers_fetches_correct_url(client: FragmentClient) -> None:
    mock_fetch = AsyncMock(return_value=FAKE_NUMBERS_HTML)
    with patch.object(client._transport, "fetch_page", mock_fetch):
        await client.get_my_numbers()

    url = mock_fetch.call_args[0][0]
    assert url.endswith("/my/numbers")


@pytest.mark.asyncio
async def test_get_my_gifts_returns_result(client: FragmentClient) -> None:
    with patch.object(client._transport, "fetch_page", AsyncMock(return_value=FAKE_GIFTS_HTML)):
        result = await client.get_my_gifts()

    assert isinstance(result, MyGiftsResult)


@pytest.mark.asyncio
async def test_get_my_gifts_fetches_correct_url(client: FragmentClient) -> None:
    mock_fetch = AsyncMock(return_value=FAKE_GIFTS_HTML)
    with patch.object(client._transport, "fetch_page", mock_fetch):
        await client.get_my_gifts()

    url = mock_fetch.call_args[0][0]
    assert url.endswith("/my/gifts")


@pytest.mark.asyncio
async def test_get_my_gifts_empty(client: FragmentClient) -> None:
    with patch.object(client._transport, "fetch_page", AsyncMock(return_value=EMPTY_HTML)):
        result = await client.get_my_gifts()

    assert isinstance(result, MyGiftsResult)
    assert result.items == []
