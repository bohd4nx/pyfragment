"""Check raw Fragment API calls and transport error handling."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from curl_cffi.requests import AsyncSession, Response

from pyfragment import FragmentClient, FragmentPageError
from pyfragment.core.transport import FragmentTransport, fragment_request, get_fragment_hash
from tests.shared import FAKE_HASH, FAKE_RESPONSE

# client.call() mocked tests


@pytest.mark.asyncio
async def test_call_returns_api_response(client: FragmentClient) -> None:
    with (
        patch("pyfragment.core.transport.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.core.transport.fragment_request", AsyncMock(return_value=FAKE_RESPONSE)),
    ):
        result = await client.call("anyMethod", {"key": "value"})

    assert result == FAKE_RESPONSE


@pytest.mark.asyncio
async def test_call_default_page_url(client: FragmentClient) -> None:
    with (
        patch("pyfragment.core.transport.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.core.transport.fragment_request", AsyncMock(return_value=FAKE_RESPONSE)),
    ):
        result = await client.call("anyMethod")

    assert result == FAKE_RESPONSE


@pytest.mark.asyncio
async def test_call_no_data(client: FragmentClient) -> None:
    mock_request = AsyncMock(return_value={})

    with (
        patch("pyfragment.core.transport.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.core.transport.fragment_request", mock_request),
    ):
        await client.call("anyMethod")

    _, _, _, sent_data = mock_request.call_args.args
    assert sent_data == {"method": "anyMethod"}


@pytest.mark.asyncio
async def test_call_merges_extra_data(client: FragmentClient) -> None:
    mock_request = AsyncMock(return_value={})

    with (
        patch("pyfragment.core.transport.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.core.transport.fragment_request", mock_request),
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


# FragmentTransport: session reuse and API hash caching


def _response(payload: dict[str, object] | None = None, status: int = 200) -> MagicMock:
    response = MagicMock(spec=Response)
    response.status_code = status
    response.json.return_value = payload or {}
    return response


def _transport_with_session(session: AsyncMock) -> FragmentTransport:
    transport = FragmentTransport({}, 30.0, {})
    transport._session = session
    return transport


@pytest.mark.asyncio
async def test_transport_caches_hash_per_page() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.post = AsyncMock(return_value=_response({"ok": 1}))
    transport = _transport_with_session(session)

    with patch("pyfragment.core.transport.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)) as mock_hash:
        await transport.call("a", None, "https://fragment.com/stars/buy")
        await transport.call("b", None, "https://fragment.com/stars/buy")
        await transport.call("c", None, "https://fragment.com/premium/gift")

    assert [c.args[1] for c in mock_hash.call_args_list] == [
        "https://fragment.com/stars/buy",
        "https://fragment.com/premium/gift",
    ]
    assert session.post.await_count == 3


@pytest.mark.asyncio
async def test_transport_refreshes_stale_hash_once() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.post = AsyncMock(side_effect=[_response(), _response(status=403), _response({"ok": 1})])
    transport = _transport_with_session(session)
    page_url = "https://fragment.com/stars/buy"

    with patch("pyfragment.core.transport.get_fragment_hash", AsyncMock(side_effect=["old", "new"])) as mock_hash:
        await transport.call("a", None, page_url)
        assert await transport.call("b", None, page_url) == {"ok": 1}

    assert mock_hash.await_count == 2
    assert transport._hashes[page_url] == "new"
    assert "hash=new" in session.post.call_args.args[0]


@pytest.mark.asyncio
async def test_transport_does_not_refresh_hash_on_rate_limit() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.post = AsyncMock(side_effect=[_response(), _response(status=429), _response(status=429), _response(status=429)])
    transport = _transport_with_session(session)
    page_url = "https://fragment.com/stars/buy"

    with (
        patch("pyfragment.core.transport.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)) as mock_hash,
        patch("pyfragment.core.transport.asyncio.sleep", AsyncMock()),
    ):
        await transport.call("a", None, page_url)
        with pytest.raises(FragmentPageError, match="429"):
            await transport.call("b", None, page_url)

    assert mock_hash.await_count == 1
    assert transport._hashes[page_url] == FAKE_HASH


@pytest.mark.asyncio
async def test_transport_failed_first_call_does_not_cache_hash() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.post = AsyncMock(return_value=_response(status=403))
    transport = _transport_with_session(session)

    with (
        patch("pyfragment.core.transport.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        pytest.raises(FragmentPageError, match="403"),
    ):
        await transport.call("a", None, "https://fragment.com/stars/buy")

    assert transport._hashes == {}


@pytest.mark.asyncio
async def test_transport_reuses_one_session_and_aclose_resets_it() -> None:
    transport = FragmentTransport({}, 30.0, {})

    first = transport._get_session()
    assert transport._get_session() is first

    transport._hashes["https://fragment.com"] = FAKE_HASH
    await transport.aclose()

    assert transport._session is None
    assert transport._hashes == {}
    assert transport._get_session() is not first
    await transport.aclose()
