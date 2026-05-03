"""Unit tests for FragmentClient.call() — raw Fragment API access."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from pyfragment import FragmentClient
from pyfragment.types import FragmentPageError
from pyfragment.utils.http import fragment_request
from tests.shared import FAKE_HASH, FAKE_RESPONSE

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


# fragment_request HTTP status tests


@pytest.mark.asyncio
async def test_fragment_request_non_200_raises() -> None:
    """fragment_request raises FragmentPageError on non-200 HTTP responses."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = 429

    session = AsyncMock(spec=httpx.AsyncClient)
    session.post = AsyncMock(return_value=response)

    with pytest.raises(FragmentPageError, match="429"):
        await fragment_request(session, FAKE_HASH, {}, {"method": "anyMethod"})
