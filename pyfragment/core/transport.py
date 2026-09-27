from __future__ import annotations

import asyncio
import logging
import random
import re
from typing import Any, cast
from urllib.parse import urlsplit, urlunsplit

from curl_cffi.requests import AsyncSession, Response

from pyfragment.core.constants import FRAGMENT_BASE_URL
from pyfragment.exceptions import FragmentPageError, ParseError

logger = logging.getLogger(__name__)


def _parent_url(page_url: str) -> str:
    # Derive the natural referer: strip the last path segment (e.g. /stars/buy → /stars).
    # The root page has no path segment to strip - rsplit would otherwise chop the URL
    # scheme itself (e.g. "https://fragment.com" -> "https:/").
    parsed = urlsplit(page_url)
    if parsed.path in ("", "/"):
        return urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
    path = parsed.path.rstrip("/").rsplit("/", 1)[0]
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


async def get_fragment_hash(
    session: AsyncSession[Any],
    page_url: str,
) -> str:
    parent_url = _parent_url(page_url) or FRAGMENT_BASE_URL

    # This is a plain page load, not an XHR call — leave Accept/Sec-Fetch-*/UA/etc. to
    # curl_cffi's impersonate="chrome" defaults, which already look like a real navigation.
    response = await session.get(page_url, headers={"referer": parent_url})

    if response.status_code != 200:
        raise FragmentPageError(
            FragmentPageError.BAD_STATUS.format(status=response.status_code, url=page_url),
            status_code=response.status_code,
        )

    match = re.search(r"(?:https://fragment\.com)?\\\\?/api\?hash=([a-f0-9]+)", response.text)
    if not match:
        raise FragmentPageError(FragmentPageError.NOT_FOUND.format(url=page_url))

    return match.group(1)


def parse_json_response(response: Response, context: str) -> dict[str, Any]:
    try:
        return cast(dict[str, Any], response.json())  # type: ignore[no-untyped-call]
    except Exception as exc:
        raise ParseError(ParseError.UNPARSEABLE.format(context=context, exc=exc)) from exc


async def fragment_request(
    session: AsyncSession[Any],
    fragment_hash: str,
    headers: dict[str, str | None],
    data: dict[str, Any],
) -> dict[str, Any]:
    for attempt in range(3):
        resp = await session.post(
            f"{FRAGMENT_BASE_URL}/api?hash={fragment_hash}",
            headers=headers,
            data=data,
        )
        if resp.status_code == 429 and attempt < 2:
            await asyncio.sleep(1 + attempt + random.uniform(0, 0.5))
            continue
        if resp.status_code != 200:
            raise FragmentPageError(
                FragmentPageError.BAD_STATUS.format(status=resp.status_code, url=f"{FRAGMENT_BASE_URL}/api"),
                status_code=resp.status_code,
            )
        return parse_json_response(resp, data.get("method", "request"))
    raise FragmentPageError(FragmentPageError.BAD_STATUS.format(status=429, url=f"{FRAGMENT_BASE_URL}/api"), status_code=429)


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
            try:
                return await fragment_request(session, cached_hash, headers, payload)
            except FragmentPageError as exc:
                if exc.status_code == 429:
                    raise
                # The cached hash may have gone stale: drop it and retry once with a fresh one.
                del self._hashes[page_url]

        fragment_hash = await get_fragment_hash(session, page_url)
        response = await fragment_request(session, fragment_hash, headers, payload)
        self._hashes[page_url] = fragment_hash
        return response
