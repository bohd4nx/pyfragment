"""Check raw Fragment API calls and transport error handling."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from curl_cffi.requests import AsyncSession, Response

from pyfragment import FragmentClient, FragmentPageError
from pyfragment.core.transport import fragment_request, get_fragment_hash
from tests.shared import FAKE_HASH, FAKE_RESPONSE

# client.call() mocked tests


@pytest.mark.asyncio
async def test_call_returns_api_response(client: FragmentClient) -> None:
    with (
        patch("pyfragment.domains.base.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.domains.base.fragment_request", AsyncMock(return_value=FAKE_RESPONSE)),
    ):
        result = await client.call("anyMethod", {"key": "value"})

    assert result == FAKE_RESPONSE


@pytest.mark.asyncio
async def test_call_default_page_url(client: FragmentClient) -> None:
    with (
        patch("pyfragment.domains.base.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.domains.base.fragment_request", AsyncMock(return_value=FAKE_RESPONSE)),
    ):
        result = await client.call("anyMethod")

    assert result == FAKE_RESPONSE


@pytest.mark.asyncio
async def test_call_no_data(client: FragmentClient) -> None:
    mock_request = AsyncMock(return_value={})

    with (
        patch("pyfragment.domains.base.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.domains.base.fragment_request", mock_request),
    ):
        await client.call("anyMethod")

    _, _, _, sent_data = mock_request.call_args.args
    assert sent_data == {"method": "anyMethod"}


@pytest.mark.asyncio
async def test_call_merges_extra_data(client: FragmentClient) -> None:
    mock_request = AsyncMock(return_value={})

    with (
        patch("pyfragment.domains.base.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.domains.base.fragment_request", mock_request),
    ):
        await client.call("anyMethod", {"key": "value", "num": 7})

    _, _, _, sent_data = mock_request.call_args.args
    assert sent_data == {"method": "anyMethod", "key": "value", "num": 7}


# fragment_request HTTP status tests


@pytest.mark.asyncio
async def test_fragment_request_non_200_raises() -> None:
    response = MagicMock(spec=Response)
    response.status_code = 429

    session = AsyncMock(spec=AsyncSession)
    session.post = AsyncMock(return_value=response)

    with pytest.raises(FragmentPageError, match="429"):
        await fragment_request(session, FAKE_HASH, {}, {"method": "anyMethod"})


# get_fragment_hash referer derivation


@pytest.mark.asyncio
@pytest.mark.parametrize("page_url", ["https://fragment.com", "https://fragment.com/"])
async def test_get_fragment_hash_root_url_referer(page_url: str) -> None:
    response = MagicMock(spec=Response)
    response.status_code = 200
    response.text = r"\/api?hash=abc123"

    session = AsyncMock(spec=AsyncSession)
    session.get = AsyncMock(return_value=response)

    assert await get_fragment_hash(session, page_url) == "abc123"
    assert session.get.call_args.kwargs["headers"]["referer"] == "https://fragment.com"


@pytest.mark.asyncio
async def test_get_fragment_hash_nested_url_referer_is_parent_path() -> None:
    response = MagicMock(spec=Response)
    response.status_code = 200
    response.text = r"\/api?hash=abc123"

    session = AsyncMock(spec=AsyncSession)
    session.get = AsyncMock(return_value=response)

    assert await get_fragment_hash(session, "https://fragment.com/stars/buy") == "abc123"
    assert session.get.call_args.kwargs["headers"]["referer"] == "https://fragment.com/stars"
