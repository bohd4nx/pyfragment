"""Unit tests for client.call() — raw Fragment API request."""

from unittest.mock import AsyncMock, patch

import pytest

from pyfragment import FragmentClient
from tests.shared import FAKE_HASH

FAKE_RESPONSE = {"status": "ok", "data": {"value": 42}}


# client.call() mocked tests


@pytest.mark.asyncio
async def test_call_returns_api_response(client: FragmentClient) -> None:
    with (
        patch("pyfragment.client.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.client.fragment_request", AsyncMock(return_value=FAKE_RESPONSE)),
    ):
        result = await client.call("anyMethod", {"key": "value"})

    assert result == FAKE_RESPONSE


@pytest.mark.asyncio
async def test_call_default_page_url(client: FragmentClient) -> None:
    """call() works without explicitly passing page_url (defaults to FRAGMENT_BASE_URL)."""
    with (
        patch("pyfragment.client.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.client.fragment_request", AsyncMock(return_value=FAKE_RESPONSE)),
    ):
        result = await client.call("anyMethod")

    assert result == FAKE_RESPONSE


@pytest.mark.asyncio
async def test_call_no_data(client: FragmentClient) -> None:
    """call() with no extra data passes only the method field."""
    mock_request = AsyncMock(return_value={})

    with (
        patch("pyfragment.client.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.client.fragment_request", mock_request),
    ):
        await client.call("anyMethod")

    _, _, _, sent_data = mock_request.call_args.args
    assert sent_data == {"method": "anyMethod"}


@pytest.mark.asyncio
async def test_call_merges_extra_data(client: FragmentClient) -> None:
    """call() merges caller-supplied data with the method field."""
    mock_request = AsyncMock(return_value={})

    with (
        patch("pyfragment.client.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.client.fragment_request", mock_request),
    ):
        await client.call("anyMethod", {"key": "value", "num": 7})

    _, _, _, sent_data = mock_request.call_args.args
    assert sent_data == {"method": "anyMethod", "key": "value", "num": 7}
