from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Any

from curl_cffi.requests import AsyncSession

from pyfragment.enums import ApiError
from pyfragment.exceptions import SessionExpiredError
from pyfragment.schemas import has_error
from pyfragment.transport.api import fragment_request, is_bad_hash, send, status_error
from pyfragment.transport.page import check_authenticated_page, get_fragment_hash, parent_url

logger = logging.getLogger(__name__)


class FragmentTransport:
    """Reusable HTTP transport for Fragment's JSON API.

    Holds one browser-impersonating session (connection pool, TLS session and cookie jar are
    reused across calls, like a real browser tab) and caches the per-page API hash, so a call
    costs one POST instead of a page load plus a POST on a fresh connection.
    """

    def __init__(self, cookies: dict[str, Any], timeout: float, headers: dict[str, str | None]) -> None:
        self._cookies = cookies
        self._timeout = timeout
        self._headers = headers
        self._session: AsyncSession[Any] | None = None
        self._hashes: dict[str, str] = {}

    def _get_session(self) -> AsyncSession[Any]:
        if self._session is None:
            self._session = AsyncSession(cookies=self._cookies, timeout=self._timeout, impersonate="chrome")
        return self._session

    async def fetch_page(self, url: str) -> str:
        """Fetch an authenticated Fragment HTML page (e.g. ``/my/usernames``)."""
        session = self._get_session()
        response = await send(session.get(url, headers={"referer": parent_url(url)}), url)
        if response.status_code != HTTPStatus.OK:
            raise status_error(response.status_code, url)
        check_authenticated_page(response.text, url)
        return response.text

    async def aclose(self) -> None:
        session, self._session = self._session, None
        self._hashes.clear()
        if session is not None:
            await session.close()

    async def call(self, method: str, data: dict[str, Any] | None, page_url: str) -> dict[str, Any]:
        payload = {"method": method, **(data or {})}
        headers = {**self._headers, "referer": page_url}
        logger.debug("Starting Fragment API call '%s' on %s", method, page_url)
        response = await self._request(page_url, headers, payload)
        logger.debug("Completed Fragment API call '%s' with response keys: %s", method, sorted(response.keys()))
        if err := response.get("error"):
            logger.debug("Fragment API call '%s' returned error: %s", method, err)
        if has_error(response, ApiError.ACCESS_DENIED):
            # Fragment answers calls made with a logged-out session or disconnected wallet this way.
            raise SessionExpiredError(SessionExpiredError.ACCESS_DENIED.format(context=method))
        return response

    async def _request(self, page_url: str, headers: dict[str, str | None], payload: dict[str, Any]) -> dict[str, Any]:
        session = self._get_session()
        retried_stale = False

        cached_hash = self._hashes.get(page_url)
        if cached_hash is not None:
            response = await fragment_request(session, cached_hash, headers, payload)
            if not is_bad_hash(response):
                return response
            # The cached hash went stale: drop it and retry once with a fresh one.
            retried_stale = True
            del self._hashes[page_url]

        fragment_hash = await get_fragment_hash(session, page_url)
        response = await fragment_request(session, fragment_hash, headers, payload)
        if is_bad_hash(response) and retried_stale:
            # Both the cached hash and a freshly fetched one were rejected: session issue.
            raise SessionExpiredError(SessionExpiredError.STALE_HASH.format(url=page_url))
        # Always cache the fresh hash: even if the response is "Bad request", the hash itself is valid.
        self._hashes[page_url] = fragment_hash
        return response
