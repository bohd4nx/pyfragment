"""fragment_request: one POST to /api, retrying only HTTP 429, and the mapping of statuses and bodies to errors."""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from curl_cffi.requests import Response
from curl_cffi.requests.exceptions import ConnectionError, Timeout

from pyfragment import FragmentAPIError, HTTPStatusError, NetworkError, ParseError, SessionExpiredError
from pyfragment.constants.fragment import FRAGMENT_API_URL, MAX_API_ATTEMPTS
from pyfragment.transport import fragment_request
from pyfragment.transport.api import is_bad_hash, parse_json_response, status_error
from tests.support import fixtures
from tests.transport.http import HASH, reply, session

PAYLOAD = {"method": "searchAuctions"}


@pytest.fixture(autouse=True)
def sleeps() -> AsyncMock:
    with patch("pyfragment.transport.api.asyncio.sleep", AsyncMock()) as sleep:
        yield sleep


async def test_posts_the_method_to_the_api_url_with_the_hash() -> None:
    fake = session(post=[reply(200, {"ok": True})])

    result = await fragment_request(fake, HASH, {"x": "1"}, PAYLOAD)

    assert result == {"ok": True}
    fake.post.assert_awaited_once_with(f"{FRAGMENT_API_URL}?hash={HASH}", headers={"x": "1"}, data=PAYLOAD)


async def test_an_error_body_with_http_200_is_returned_not_raised() -> None:
    body = fixtures.response("invalid_method.json")
    assert await fragment_request(session(post=[reply(200, body)]), HASH, {}, PAYLOAD) == body


class TestRateLimit:
    async def test_429_is_retried_until_it_succeeds(self, sleeps: AsyncMock) -> None:
        fake = session(post=[reply(429), reply(429), reply(200, {"req_id": "r"})])

        assert await fragment_request(fake, HASH, {}, PAYLOAD) == {"req_id": "r"}
        assert fake.post.await_count == 3
        assert sleeps.await_count == 2

    async def test_a_retry_is_logged(self, sleeps: AsyncMock, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.DEBUG, logger="pyfragment")

        await fragment_request(session(post=[reply(429), reply(200)]), HASH, {}, PAYLOAD)

        assert "Rate limited (attempt=1/" in caplog.text

    async def test_backoff_grows_with_the_attempt_and_is_jittered(self, sleeps: AsyncMock) -> None:
        fake = session(post=[reply(429), reply(429), reply(200)])

        with patch("pyfragment.transport.api.random.uniform", return_value=0.25) as jitter:
            await fragment_request(fake, HASH, {}, PAYLOAD)

        assert [call.args[0] for call in sleeps.await_args_list] == [1.25, 2.25]
        jitter.assert_called_with(0, 0.5)

    async def test_gives_up_after_the_last_attempt_with_a_retryable_error(self, sleeps: AsyncMock) -> None:
        fake = session(post=[reply(429)] * MAX_API_ATTEMPTS)

        with pytest.raises(HTTPStatusError) as exc_info:
            await fragment_request(fake, HASH, {}, PAYLOAD)

        assert fake.post.await_count == MAX_API_ATTEMPTS
        assert sleeps.await_count == MAX_API_ATTEMPTS - 1
        assert exc_info.value.status == 429 and exc_info.value.retryable

    @pytest.mark.parametrize("status", [500, 502, 503, 404])
    async def test_other_statuses_are_not_retried(self, status: int, sleeps: AsyncMock) -> None:
        fake = session(post=[reply(status), reply(200)])

        with pytest.raises(HTTPStatusError):
            await fragment_request(fake, HASH, {}, PAYLOAD)

        assert fake.post.await_count == 1
        sleeps.assert_not_awaited()


class TestStatusMapping:
    @pytest.mark.parametrize("status", [500, 502, 503, 504])
    async def test_server_errors_are_retryable_and_do_not_blame_the_cookies(self, status: int) -> None:
        with pytest.raises(HTTPStatusError) as exc_info:
            await fragment_request(session(post=[reply(status)]), HASH, {}, PAYLOAD)

        assert exc_info.value.status == status and exc_info.value.retryable
        assert "temporarily unavailable" in str(exc_info.value)
        assert "cookie" not in str(exc_info.value).lower()

    @pytest.mark.parametrize("status", [401, 403])
    async def test_a_rejected_session_asks_for_new_cookies(self, status: int) -> None:
        with pytest.raises(SessionExpiredError, match="refresh your cookies") as exc_info:
            await fragment_request(session(post=[reply(status)]), HASH, {}, PAYLOAD)

        assert not exc_info.value.retryable
        assert str(status) in str(exc_info.value)

    @pytest.mark.parametrize("status", [400, 404, 418])
    async def test_other_client_errors_are_plain_and_final(self, status: int) -> None:
        with pytest.raises(HTTPStatusError) as exc_info:
            await fragment_request(session(post=[reply(status)]), HASH, {}, PAYLOAD)

        assert exc_info.value.status == status and not exc_info.value.retryable

    def test_status_error_returns_instead_of_raising(self) -> None:
        assert isinstance(status_error(403, "u"), SessionExpiredError)
        assert isinstance(status_error(500, "u"), HTTPStatusError)


class TestNetworkErrors:
    @pytest.mark.parametrize("error", [ConnectionError("reset"), Timeout("slow")])
    async def test_a_failure_to_reach_fragment_is_a_retryable_network_error(self, error: Exception) -> None:
        fake = session(post=[error])

        with pytest.raises(NetworkError, match=str(error)) as exc_info:
            await fragment_request(fake, HASH, {}, PAYLOAD)

        assert exc_info.value.retryable and isinstance(exc_info.value, FragmentAPIError)
        assert exc_info.value.__cause__ is error
        assert FRAGMENT_API_URL in str(exc_info.value)
        assert fake.post.await_count == 1


class TestParsing:
    async def test_a_body_that_is_not_json_is_a_parse_error_naming_the_method(self) -> None:
        response = reply(200)
        response.json.side_effect = ValueError("no json")

        with pytest.raises(ParseError, match="searchAuctions"):
            await fragment_request(session(post=[response]), HASH, {}, PAYLOAD)

    def test_the_context_defaults_to_request_when_the_payload_has_no_method(self) -> None:
        response = MagicMock(spec=Response)
        response.json.side_effect = ValueError("no json")

        with pytest.raises(ParseError, match="'x'"):
            parse_json_response(response, "x")

    async def test_the_default_context_is_request(self) -> None:
        response = reply(200)
        response.json.side_effect = ValueError("no json")

        with pytest.raises(ParseError, match="'request'"):
            await fragment_request(session(post=[response]), HASH, {}, {})


class TestBadHash:
    @pytest.mark.parametrize("body", [{"error": "Bad request"}, {"error": "bad REQUEST."}])
    def test_fragment_rejecting_the_hash(self, body: dict[str, str]) -> None:
        assert is_bad_hash(body)

    @pytest.mark.parametrize("body", [{}, {"ok": True}, {"error": "Access denied"}, fixtures.response("invalid_method.json")])
    def test_anything_else(self, body: dict[str, object]) -> None:
        assert not is_bad_hash(body)
