from __future__ import annotations

import re
from http import HTTPStatus
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from curl_cffi.requests import AsyncSession

from pyfragment.exceptions import SessionExpiredError
from pyfragment.transport.api import send, status_error

API_HASH_RE = re.compile(r"(?:https://fragment\.com)?\\\\?/api\?hash=([a-f0-9]+)")


def parent_url(page_url: str) -> str:
    # Derive the natural referer: strip the last path segment (e.g. /stars/buy → /stars).
    # The root page has no path segment to strip - rsplit would otherwise chop the URL
    # scheme itself (e.g. "https://fragment.com" -> "https:/").
    parsed = urlsplit(page_url)
    if parsed.path in ("", "/"):
        return urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
    path = parsed.path.rstrip("/").rsplit("/", 1)[0]
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


async def get_fragment_hash(session: AsyncSession[Any], page_url: str) -> str:
    """Load a Fragment page and extract the API hash its frontend embeds for ``/api?hash=...`` calls."""
    referer = parent_url(page_url)

    # This is a plain page load, not an XHR call — leave Accept/Sec-Fetch-*/UA/etc. to
    # curl_cffi's impersonate="chrome" defaults, which already look like a real navigation.
    response = await send(session.get(page_url, headers={"referer": referer}), page_url)

    if response.status_code != HTTPStatus.OK:
        raise status_error(response.status_code, page_url)

    match = API_HASH_RE.search(response.text)
    if not match:
        # Logged-out pages don't embed the hash (a login redirect lands on one of them too).
        raise SessionExpiredError(SessionExpiredError.NO_HASH.format(url=page_url))

    return match.group(1)
