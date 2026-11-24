"""Page loads: finding the API hash, the referer sent with it, and telling a logged-in page from a logged-out one."""

import pytest
from curl_cffi.requests.exceptions import Timeout

from pyfragment import HTTPStatusError, NetworkError, SessionExpiredError
from pyfragment.constants.fragment import FRAGMENT_BASE_URL, PREMIUM_PAGE, STARS_PAGE
from pyfragment.transport import get_fragment_hash
from pyfragment.transport.page import check_authenticated_page, parent_url
from tests.transport.http import HASH, LOGGED_IN_PAGE, LOGGED_OUT_PAGE, reply, session


class TestParentUrl:
    @pytest.mark.parametrize(
        ("url", "parent"),
        [
            (STARS_PAGE, "https://fragment.com/stars"),
            ("https://fragment.com/stars/buy/", "https://fragment.com/stars"),
            ("https://fragment.com/my/assets", "https://fragment.com/my"),
            ("https://fragment.com/stars", "https://fragment.com"),
            ("https://fragment.com/stars/buy?x=1#top", "https://fragment.com/stars"),
        ],
    )
    def test_strips_the_last_path_segment(self, url: str, parent: str) -> None:
        assert parent_url(url) == parent

    @pytest.mark.parametrize("url", [FRAGMENT_BASE_URL, FRAGMENT_BASE_URL + "/"])
    def test_the_root_page_is_its_own_parent_and_keeps_its_scheme(self, url: str) -> None:
        assert parent_url(url) == "https://fragment.com"


class TestGetFragmentHash:
    @pytest.mark.parametrize(
        "html",
        [
            LOGGED_IN_PAGE,
            r'"url":"https:\/\/fragment.com\/api?hash=' + HASH + '"',
            rf"https:\/\/fragment.com\/api?hash={HASH}",
        ],
    )
    async def test_extracts_the_hash_from_the_page_markup(self, html: str) -> None:
        assert await get_fragment_hash(session(get=[reply(200, text=html)]), STARS_PAGE) == HASH

    async def test_loads_the_page_with_its_parent_as_referer(self) -> None:
        fake = session(get=[reply(200, text=LOGGED_IN_PAGE)])

        await get_fragment_hash(fake, PREMIUM_PAGE)

        fake.get.assert_awaited_once_with(PREMIUM_PAGE, headers={"referer": "https://fragment.com/premium"})

    async def test_the_root_page_gets_a_valid_referer(self) -> None:
        fake = session(get=[reply(200, text=LOGGED_IN_PAGE)])

        await get_fragment_hash(fake, FRAGMENT_BASE_URL)

        assert fake.get.await_args.kwargs["headers"] == {"referer": "https://fragment.com"}

    async def test_a_page_without_the_hash_means_a_logged_out_session(self) -> None:
        with pytest.raises(SessionExpiredError, match="not logged in"):
            await get_fragment_hash(session(get=[reply(200, text="<html>Log in</html>")]), STARS_PAGE)

    @pytest.mark.parametrize("status", [401, 403])
    async def test_a_rejected_session(self, status: int) -> None:
        with pytest.raises(SessionExpiredError, match="refresh your cookies"):
            await get_fragment_hash(session(get=[reply(status)]), STARS_PAGE)

    async def test_a_bad_status_is_reported_and_a_server_error_is_retryable(self) -> None:
        with pytest.raises(HTTPStatusError) as exc_info:
            await get_fragment_hash(session(get=[reply(502)]), STARS_PAGE)
        assert exc_info.value.status == 502 and exc_info.value.retryable

        with pytest.raises(HTTPStatusError) as exc_info:
            await get_fragment_hash(session(get=[reply(404)]), STARS_PAGE)
        assert not exc_info.value.retryable

    async def test_network_failures_are_not_retried(self) -> None:
        fake = session(get=[Timeout("slow")])

        with pytest.raises(NetworkError, match="slow") as exc_info:
            await get_fragment_hash(fake, STARS_PAGE)

        assert exc_info.value.retryable and STARS_PAGE in str(exc_info.value)
        assert fake.get.await_count == 1


class TestCheckAuthenticatedPage:
    def test_a_logged_in_page_passes(self) -> None:
        check_authenticated_page(LOGGED_IN_PAGE, STARS_PAGE)

    @pytest.mark.parametrize("marker", ['"logged_in":true', '"logged_in" : true', '"logged_in"\n:\ttrue'])
    def test_the_logged_in_marker_tolerates_whitespace(self, marker: str) -> None:
        check_authenticated_page(LOGGED_OUT_PAGE + f"{{{marker}}}", STARS_PAGE)

    def test_an_unescaped_api_path_is_not_the_hash_fragment_embeds(self) -> None:
        with pytest.raises(SessionExpiredError, match="API hash"):
            check_authenticated_page(f'/api?hash={HASH} {{"logged_in": true}}', STARS_PAGE)

    def test_no_api_hash_means_the_page_is_not_fragment_s_or_the_layout_changed(self) -> None:
        with pytest.raises(SessionExpiredError, match="API hash") as exc_info:
            check_authenticated_page('{"logged_in": true}', STARS_PAGE)
        assert STARS_PAGE in str(exc_info.value)

    def test_a_hash_without_the_logged_in_marker_is_the_logged_out_main_page(self) -> None:
        # Fragment answers logged-out /my/* requests with the main page, which has a hash too.
        with pytest.raises(SessionExpiredError, match="logged-out page"):
            check_authenticated_page(LOGGED_OUT_PAGE, "https://fragment.com/my/assets")

    @pytest.mark.parametrize("html", ['{"logged_in": false}', '{"logged_in": "true"}'])
    def test_logged_in_must_be_the_literal_true(self, html: str) -> None:
        with pytest.raises(SessionExpiredError, match="logged-out page"):
            check_authenticated_page(LOGGED_OUT_PAGE + html, STARS_PAGE)
