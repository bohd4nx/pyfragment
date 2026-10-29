"""Fragment transport errors, session expiry detection, recipient checks, error classification and logging."""

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from curl_cffi.requests import AsyncSession, Response
from curl_cffi.requests.exceptions import ConnectionError, Timeout

import pyfragment.domains.payments.flow as _flow_mod
from pyfragment import (
    AlreadySubscribedError,
    AnonymousNumberError,
    ChainError,
    FragmentAPIError,
    FragmentClient,
    HTTPStatusError,
    InsufficientBalanceError,
    NetworkError,
    SessionExpiredError,
    UserNotFoundError,
)
from pyfragment.constants import GRAM_CURRENCY, STARS_PAGE
from pyfragment.enums import ApiMethod
from pyfragment.exceptions import ProviderError, TransactionError
from pyfragment.transport import fragment_request, get_fragment_hash
from tests.shared import FAKE_ACCOUNT, FAKE_HASH, FAKE_RECIPIENT, FAKE_TRANSACTION


def _response(status: int = 200, payload: dict[str, object] | None = None, text: str = "") -> MagicMock:
    response = MagicMock(spec=Response)
    response.status_code = status
    response.json.return_value = payload or {}
    response.text = text
    return response


def _session(*answers: object, method: str = "post") -> AsyncMock:
    session = AsyncMock(spec=AsyncSession)
    setattr(session, method, AsyncMock(side_effect=list(answers)))
    return session


@contextmanager
def no_sleep() -> Iterator[None]:
    with patch("pyfragment.transport.api.asyncio.sleep", AsyncMock()):
        yield


# Fragment /api: only HTTP 429 is repeated (Fragment didn't process the call); everything else is reported


@pytest.mark.asyncio
@pytest.mark.parametrize("method", [ApiMethod.SEARCH_STARS_RECIPIENT, ApiMethod.INIT_BUY_STARS_REQUEST])
async def test_server_error_is_not_retried(method: str) -> None:
    # Retrying is the caller's call: the error says whether it makes sense.
    session = _session(_response(500), _response(200))
    with no_sleep(), pytest.raises(HTTPStatusError) as exc_info:
        await fragment_request(session, FAKE_HASH, {}, {"method": method})
    assert session.post.await_count == 1
    assert exc_info.value.status == 500 and exc_info.value.retryable


@pytest.mark.asyncio
async def test_rate_limit_is_retried_for_any_call() -> None:
    session = _session(_response(429), _response(200, {"req_id": "r"}))
    with no_sleep():
        assert await fragment_request(session, FAKE_HASH, {}, {"method": ApiMethod.INIT_BUY_STARS_REQUEST}) == {"req_id": "r"}


@pytest.mark.asyncio
async def test_network_error_raises_network_error() -> None:
    session = _session(ConnectionError("reset"))
    with no_sleep(), pytest.raises(NetworkError, match="reset") as exc_info:
        await fragment_request(session, FAKE_HASH, {}, {"method": ApiMethod.SEARCH_AUCTIONS})
    assert exc_info.value.retryable and isinstance(exc_info.value, FragmentAPIError)
    assert session.post.await_count == 1


@pytest.mark.asyncio
async def test_server_error_does_not_blame_the_cookies() -> None:
    session = _session(*[_response(503)] * 3)
    with no_sleep(), pytest.raises(HTTPStatusError) as exc_info:
        await fragment_request(session, FAKE_HASH, {}, {"method": ApiMethod.SEARCH_STARS_RECIPIENT})
    assert session.post.await_count == 1
    assert "temporarily unavailable" in str(exc_info.value)
    assert "cookie" not in str(exc_info.value).lower()


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [401, 403])
async def test_rejected_session_raises_session_expired(status: int) -> None:
    with no_sleep(), pytest.raises(SessionExpiredError, match="refresh your cookies") as exc_info:
        await fragment_request(_session(_response(status)), FAKE_HASH, {}, {"method": ApiMethod.SEARCH_AUCTIONS})
    assert not exc_info.value.retryable


@pytest.mark.asyncio
async def test_other_client_errors_are_plain_status_errors() -> None:
    with no_sleep(), pytest.raises(HTTPStatusError) as exc_info:
        await fragment_request(_session(_response(404)), FAKE_HASH, {}, {"method": ApiMethod.SEARCH_AUCTIONS})
    assert exc_info.value.status == 404 and not exc_info.value.retryable


# Fragment pages


@pytest.mark.asyncio
async def test_page_without_the_api_hash_means_a_logged_out_session() -> None:
    session = _session(_response(200, text="<html>Log in</html>"), method="get")
    with pytest.raises(SessionExpiredError, match="not logged in"):
        await get_fragment_hash(session, STARS_PAGE)


@pytest.mark.asyncio
async def test_page_load_failures_are_not_retried() -> None:
    with pytest.raises(HTTPStatusError) as exc_info:
        await get_fragment_hash(_session(_response(502), method="get"), STARS_PAGE)
    assert exc_info.value.retryable
    with pytest.raises(NetworkError, match="slow"):
        await get_fragment_hash(_session(Timeout("slow"), method="get"), STARS_PAGE)


@pytest.mark.asyncio
async def test_access_denied_answer_raises_session_expired(client: FragmentClient) -> None:
    with (
        patch("pyfragment.transport.session.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.transport.session.fragment_request", AsyncMock(return_value={"error": "Access denied"})),
    ):
        with pytest.raises(SessionExpiredError, match="updateLoginCodes"):
            await client.call(ApiMethod.UPDATE_LOGIN_CODES, {})


@pytest.mark.asyncio
async def test_missing_request_id_raises_session_expired(client: FragmentClient) -> None:
    call_mock = AsyncMock(side_effect=[{"found": {"recipient": FAKE_RECIPIENT}}, {}, {}])
    with patch.object(client, "call", call_mock), pytest.raises(SessionExpiredError, match="request ID"):
        await client.purchase_stars("@user", amount=500)


# Anonymous numbers


@pytest.mark.asyncio
async def test_toggle_login_codes_failure_raises_anonymous_number_error(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(return_value={"error": "Number &quot;888&quot; is not yours"})):
        with pytest.raises(AnonymousNumberError, match='Number "888" is not yours'):
            await client.toggle_login_codes("+888", can_receive=False)


# Recipient checks


@pytest.mark.asyncio
async def test_check_stars_recipient_returns_what_fragment_found(client: FragmentClient) -> None:
    found = {"recipient": FAKE_RECIPIENT, "name": "Pavel &amp; Co", "photo": "<img src='x'>", "myself": False}
    call_mock = AsyncMock(return_value={"found": found})
    with patch.object(client, "call", call_mock):
        recipient = await client.check_stars_recipient("https://t.me/durov")

    assert (recipient.recipient, recipient.username, recipient.name) == (FAKE_RECIPIENT, "https://t.me/durov", "Pavel & Co")
    assert recipient.photo == "<img src='x'>" and recipient.myself is False
    assert call_mock.await_args.args[0] == ApiMethod.SEARCH_STARS_RECIPIENT
    assert call_mock.await_args.args[1] == {"query": "https://t.me/durov", "quantity": ""}  # sent as typed
    call_mock.assert_awaited_once()  # a check never starts a purchase


@pytest.mark.asyncio
async def test_check_premium_recipient_reports_an_active_subscription(client: FragmentClient) -> None:
    answer = {"error": "This account is already subscribed to Telegram Premium."}
    with patch.object(client, "call", AsyncMock(return_value=answer)):
        with pytest.raises(AlreadySubscribedError):
            await client.check_premium_recipient("@user", months=6)


@pytest.mark.asyncio
async def test_check_recipient_not_found(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(return_value={"found": {}})):
        with pytest.raises(UserNotFoundError):
            await client.check_stars_recipient("@ghost")


@pytest.mark.asyncio
async def test_check_premium_recipient_not_found(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(return_value={"found": {}})):
        with pytest.raises(UserNotFoundError):
            await client.check_premium_recipient("@ghost", months=3)


# The exception hierarchy


def test_chain_errors_are_not_fragment_api_errors() -> None:
    for error_cls in (InsufficientBalanceError, ProviderError, TransactionError):
        assert issubclass(error_cls, ChainError) and not issubclass(error_cls, FragmentAPIError)


# Logging: the library doesn't log what it raises


@pytest.mark.asyncio
async def test_expected_failures_are_not_logged_as_errors(client: FragmentClient, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger="pyfragment")
    with patch.object(client, "call", AsyncMock(return_value={"found": {}})), pytest.raises(UserNotFoundError):
        await client.purchase_stars("@ghost", amount=500)

    low_balance = AsyncMock(side_effect=InsufficientBalanceError(0, 1, GRAM_CURRENCY))  # type: ignore[arg-type]
    call_mock = AsyncMock(side_effect=[{"found": {"recipient": FAKE_RECIPIENT}}, {}, {"req_id": "r"}, FAKE_TRANSACTION])
    with (
        patch.object(client, "call", call_mock),
        patch.object(client.ton_wallet, "account_info", return_value=FAKE_ACCOUNT),
        patch.object(_flow_mod, "process_transaction", low_balance),
        pytest.raises(InsufficientBalanceError),
    ):
        await client.purchase_stars("@user", amount=500)

    assert [r for r in caplog.records if r.levelno >= logging.WARNING] == []
