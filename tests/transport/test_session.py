"""FragmentTransport: the session it owns, the per-page hash cache with its stale-hash retry, and error mapping."""

from collections.abc import AsyncIterator, Iterator
from unittest.mock import AsyncMock, patch

import pytest

from pyfragment import HTTPStatusError, NetworkError, SessionExpiredError
from pyfragment.constants.fragment import BASE_HEADERS, FRAGMENT_API_URL, PREMIUM_PAGE, STARS_PAGE
from pyfragment.transport import FragmentTransport
from tests.support import fixtures
from tests.support.data import COOKIES
from tests.transport.http import HASH, LOGGED_IN_PAGE, LOGGED_OUT_PAGE, reply, session

FRESH_HASH = "fffeee000111"
BAD_REQUEST = {"error": "Bad request"}


def page(hash_: str = HASH) -> AsyncMock:
    return reply(200, text=LOGGED_IN_PAGE.replace(HASH, hash_))


@pytest.fixture(autouse=True)
def sleeps() -> Iterator[AsyncMock]:
    with patch("pyfragment.transport.api.asyncio.sleep", AsyncMock()) as sleep:
        yield sleep


@pytest.fixture
async def transport() -> AsyncIterator[FragmentTransport]:
    instance = FragmentTransport(COOKIES, 30.0, {"x-test": "1"})
    yield instance
    await instance.aclose()


def use(transport: FragmentTransport, fake: AsyncMock) -> AsyncMock:
    transport._session = fake
    return fake


def hashes_posted(fake: AsyncMock) -> list[str]:
    return [call.args[0].split("hash=")[1] for call in fake.post.await_args_list]


class TestCall:
    async def test_sends_the_method_with_the_data_and_the_page_as_referer(self, transport: FragmentTransport) -> None:
        fake = use(transport, session(get=[page()], post=[reply(200, {"ok": 1})]))

        result = await transport.call("searchAuctions", {"query": "a"}, STARS_PAGE)

        assert result == {"ok": 1}
        fake.post.assert_awaited_once_with(
            f"{FRAGMENT_API_URL}?hash={HASH}",
            headers={"x-test": "1", "referer": STARS_PAGE},
            data={"method": "searchAuctions", "query": "a"},
        )

    async def test_no_data_sends_just_the_method(self, transport: FragmentTransport) -> None:
        fake = use(transport, session(get=[page()], post=[reply(200, {})]))

        await transport.call("logOut", None, STARS_PAGE)

        assert fake.post.await_args.kwargs["data"] == {"method": "logOut"}

    async def test_the_method_cannot_be_overridden_by_the_data(self, transport: FragmentTransport) -> None:
        fake = use(transport, session(get=[page()], post=[reply(200, {})]))

        await transport.call("real", {"method": "fake"}, STARS_PAGE)

        # The data is merged after the method, as the library never passes one; this pins the current order.
        assert fake.post.await_args.kwargs["data"]["method"] == "fake"

    async def test_the_configured_headers_are_not_mutated(self) -> None:
        headers: dict[str, str | None] = dict(BASE_HEADERS)
        instance = FragmentTransport(COOKIES, 30.0, headers)
        use(instance, session(get=[page()], post=[reply(200, {})]))

        await instance.call("m", None, STARS_PAGE)

        assert "referer" not in headers

    async def test_an_error_body_is_returned_for_the_caller_to_map(self, transport: FragmentTransport) -> None:
        body = fixtures.response("invalid_method.json")
        use(transport, session(get=[page()], post=[reply(200, body)]))

        assert await transport.call("nope", None, STARS_PAGE) == body

    async def test_access_denied_means_the_session_or_wallet_is_gone(self, transport: FragmentTransport) -> None:
        use(transport, session(get=[page()], post=[reply(200, {"error": "Access denied"})]))

        with pytest.raises(SessionExpiredError, match="'updateLoginCodes'") as exc_info:
            await transport.call("updateLoginCodes", None, STARS_PAGE)

        assert not exc_info.value.retryable

    async def test_a_network_error_while_loading_the_page(self, transport: FragmentTransport) -> None:
        from curl_cffi.requests.exceptions import ConnectionError

        use(transport, session(get=[ConnectionError("down")]))

        with pytest.raises(NetworkError):
            await transport.call("m", None, STARS_PAGE)

    async def test_http_errors_from_the_api_propagate(self, transport: FragmentTransport) -> None:
        use(transport, session(get=[page()], post=[reply(503)]))

        with pytest.raises(HTTPStatusError) as exc_info:
            await transport.call("m", None, STARS_PAGE)

        assert exc_info.value.retryable

    async def test_a_logged_out_page_without_a_hash(self, transport: FragmentTransport) -> None:
        use(transport, session(get=[reply(200, text="<html>Log in</html>")]))

        with pytest.raises(SessionExpiredError, match="not logged in"):
            await transport.call("m", None, STARS_PAGE)


class TestHashCache:
    async def test_the_hash_is_loaded_once_per_page(self, transport: FragmentTransport) -> None:
        fake = use(transport, session(get=[page()], post=[reply(200, {}), reply(200, {}), reply(200, {})]))

        for _ in range(3):
            await transport.call("m", None, STARS_PAGE)

        assert fake.get.await_count == 1
        assert hashes_posted(fake) == [HASH] * 3

    async def test_each_page_has_its_own_hash(self, transport: FragmentTransport) -> None:
        fake = use(transport, session(get=[page(HASH), page(FRESH_HASH)], post=[reply(200, {})] * 3))

        await transport.call("m", None, STARS_PAGE)
        await transport.call("m", None, PREMIUM_PAGE)
        await transport.call("m", None, STARS_PAGE)

        assert [call.args[0] for call in fake.get.await_args_list] == [STARS_PAGE, PREMIUM_PAGE]
        assert hashes_posted(fake) == [HASH, FRESH_HASH, HASH]

    async def test_a_failed_first_call_does_not_cache_the_hash(self, transport: FragmentTransport) -> None:
        fake = use(transport, session(get=[page(), page()], post=[reply(500), reply(200, {})]))

        with pytest.raises(HTTPStatusError):
            await transport.call("m", None, STARS_PAGE)
        await transport.call("m", None, STARS_PAGE)

        assert fake.get.await_count == 2

    async def test_a_rate_limited_call_keeps_the_cached_hash(self, transport: FragmentTransport) -> None:
        fake = use(transport, session(get=[page()], post=[reply(200, {}), reply(429), reply(200, {"ok": 1})]))

        await transport.call("m", None, STARS_PAGE)
        assert await transport.call("m", None, STARS_PAGE) == {"ok": 1}

        assert fake.get.await_count == 1


class TestStaleHash:
    async def test_a_rejected_cached_hash_is_replaced_and_the_call_retried_once(self, transport: FragmentTransport) -> None:
        fake = use(
            transport,
            session(
                get=[page(HASH), page(FRESH_HASH)],
                post=[reply(200, {}), reply(200, BAD_REQUEST), reply(200, {"ok": 1})],
            ),
        )

        await transport.call("m", None, STARS_PAGE)
        assert await transport.call("m", None, STARS_PAGE) == {"ok": 1}

        assert hashes_posted(fake) == [HASH, HASH, FRESH_HASH]
        assert transport._hashes[STARS_PAGE] == FRESH_HASH

    async def test_a_fresh_hash_that_is_rejected_too_means_the_session_is_bad(self, transport: FragmentTransport) -> None:
        use(
            transport,
            session(
                get=[page(HASH), page(FRESH_HASH)],
                post=[reply(200, {}), reply(200, BAD_REQUEST), reply(200, BAD_REQUEST)],
            ),
        )

        await transport.call("m", None, STARS_PAGE)
        with pytest.raises(SessionExpiredError, match="freshly fetched API hash") as exc_info:
            await transport.call("m", None, STARS_PAGE)

        assert STARS_PAGE in str(exc_info.value)

    async def test_bad_request_on_a_first_hash_is_returned_and_the_hash_is_kept(self, transport: FragmentTransport) -> None:
        # Without a cached hash there is nothing stale to blame: "Bad request" may be a malformed call.
        fake = use(transport, session(get=[page()], post=[reply(200, BAD_REQUEST), reply(200, {})]))

        assert await transport.call("m", None, STARS_PAGE) == BAD_REQUEST
        await transport.call("m", None, STARS_PAGE)

        assert fake.get.await_count == 1
        assert hashes_posted(fake) == [HASH, HASH]


class TestFetchPage:
    async def test_returns_the_html_of_a_logged_in_page(self, transport: FragmentTransport) -> None:
        fake = use(transport, session(get=[reply(200, text=LOGGED_IN_PAGE)]))

        assert await transport.fetch_page("https://fragment.com/my/assets") == LOGGED_IN_PAGE
        fake.get.assert_awaited_once_with("https://fragment.com/my/assets", headers={"referer": "https://fragment.com/my"})

    async def test_a_logged_out_page_is_a_session_error(self, transport: FragmentTransport) -> None:
        use(transport, session(get=[reply(200, text=LOGGED_OUT_PAGE)]))

        with pytest.raises(SessionExpiredError, match="logged-out page"):
            await transport.fetch_page("https://fragment.com/my/usernames")

    @pytest.mark.parametrize(("status", "error"), [(403, SessionExpiredError), (404, HTTPStatusError), (503, HTTPStatusError)])
    async def test_error_statuses(self, transport: FragmentTransport, status: int, error: type[Exception]) -> None:
        use(transport, session(get=[reply(status)]))

        with pytest.raises(error):
            await transport.fetch_page(STARS_PAGE)


class TestSession:
    async def test_the_session_is_created_lazily_with_the_cookies_and_timeout(self) -> None:
        with patch("pyfragment.transport.session.AsyncSession") as session_cls:
            instance = FragmentTransport(COOKIES, 12.5, {})
            session_cls.assert_not_called()

            instance._get_session()

        session_cls.assert_called_once_with(cookies=COOKIES, timeout=12.5, impersonate="chrome")

    async def test_one_session_is_reused_across_calls(self) -> None:
        with patch("pyfragment.transport.session.AsyncSession") as session_cls:
            instance = FragmentTransport(COOKIES, 30.0, {})

            assert instance._get_session() is instance._get_session()

        assert session_cls.call_count == 1

    async def test_aclose_closes_the_session_and_forgets_the_hashes(self) -> None:
        instance = FragmentTransport(COOKIES, 30.0, {})
        fake = use(instance, session(get=[page(), page()], post=[reply(200, {}), reply(200, {})]))
        fake.close = AsyncMock()
        await instance.call("m", None, STARS_PAGE)

        await instance.aclose()

        fake.close.assert_awaited_once()
        assert instance._session is None and instance._hashes == {}

    async def test_aclose_is_idempotent_and_safe_before_any_call(self) -> None:
        instance = FragmentTransport(COOKIES, 30.0, {})
        await instance.aclose()
        await instance.aclose()

    async def test_a_closed_transport_opens_a_new_session_and_reloads_the_hash(self) -> None:
        instance = FragmentTransport(COOKIES, 30.0, {})
        first = use(instance, session(get=[page()], post=[reply(200, {})]))
        first.close = AsyncMock()
        await instance.call("m", None, STARS_PAGE)
        await instance.aclose()

        second = session(get=[page()], post=[reply(200, {})])
        with patch("pyfragment.transport.session.AsyncSession", return_value=second):
            await instance.call("m", None, STARS_PAGE)

        assert second.get.await_count == 1
