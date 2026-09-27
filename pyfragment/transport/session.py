from __future__ import annotations

import logging
from typing import Any

from curl_cffi.requests import AsyncSession

from pyfragment.transport.api import fragment_request, is_bad_hash
from pyfragment.transport.page import get_fragment_hash

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

    async def aclose(self) -> None:
        session, self._session = self._session, None
        self._hashes.clear()
        if session is not None:
            await session.close()

    async def call(self, method: str, data: dict[str, Any] | None, page_url: str) -> dict[str, Any]:
        payload = {"method": method, **(data or {})}
        headers = {**self._headers, "referer": page_url}
        logger.debug("Starting Fragment API call '%s' on %s", method, page_url)
        try:
            response = await self._request(page_url, headers, payload)
        except Exception:
            logger.exception("Failed to call Fragment API method '%s' on %s", method, page_url)
            raise
        logger.debug("Completed Fragment API call '%s' with response keys: %s", method, sorted(response.keys()))
        return response

    async def _request(self, page_url: str, headers: dict[str, str | None], payload: dict[str, Any]) -> dict[str, Any]:
        session = self._get_session()

        cached_hash = self._hashes.get(page_url)
        if cached_hash is not None:
            response = await fragment_request(session, cached_hash, headers, payload)
            if not is_bad_hash(response):
                return response
            # The cached hash went stale: drop it and retry once with a fresh one.
            del self._hashes[page_url]

        fragment_hash = await get_fragment_hash(session, page_url)
        response = await fragment_request(session, fragment_hash, headers, payload)
        if not is_bad_hash(response):
            self._hashes[page_url] = fragment_hash
        return response
