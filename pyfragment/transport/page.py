from __future__ import annotations

import re
from http import HTTPStatus
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from curl_cffi.requests import AsyncSession

from pyfragment.core.constants import FRAGMENT_BASE_URL
from pyfragment.exceptions import FragmentPageError

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
    referer = parent_url(page_url) or FRAGMENT_BASE_URL

    # This is a plain page load, not an XHR call — leave Accept/Sec-Fetch-*/UA/etc. to
    # curl_cffi's impersonate="chrome" defaults, which already look like a real navigation.
    response = await session.get(page_url, headers={"referer": referer})

    if response.status_code != HTTPStatus.OK:
        raise FragmentPageError(FragmentPageError.BAD_STATUS.format(status=response.status_code, url=page_url))

    match = API_HASH_RE.search(response.text)
    if not match:
        raise FragmentPageError(FragmentPageError.NOT_FOUND.format(url=page_url))

    return match.group(1)
