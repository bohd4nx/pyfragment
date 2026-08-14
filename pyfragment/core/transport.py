from __future__ import annotations

import asyncio
import random
import re
from typing import Any, cast
from urllib.parse import urlsplit, urlunsplit

from curl_cffi.requests import AsyncSession, Response

from pyfragment.core.constants import FRAGMENT_BASE_URL
from pyfragment.exceptions import FragmentPageError, ParseError


def _parent_url(page_url: str) -> str:
    # Derive the natural referer: strip the last path segment (e.g. /stars/buy → /stars).
    # The root page has no path segment to strip - rsplit would otherwise chop the URL
    # scheme itself (e.g. "https://fragment.com" -> "https:/").
    parsed = urlsplit(page_url)
    if parsed.path in ("", "/"):
        return urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
    return page_url.rsplit("/", 1)[0]


async def get_fragment_hash(
    session: AsyncSession[Any],
    page_url: str,
) -> str:
    parent_url = _parent_url(page_url) or FRAGMENT_BASE_URL

    # This is a plain page load, not an XHR call — leave Accept/Sec-Fetch-*/UA/etc. to
    # curl_cffi's impersonate="chrome" defaults, which already look like a real navigation.
    response = await session.get(page_url, headers={"referer": parent_url})

    if response.status_code != 200:
        raise FragmentPageError(FragmentPageError.BAD_STATUS.format(status=response.status_code, url=page_url))

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
                FragmentPageError.BAD_STATUS.format(status=resp.status_code, url=f"{FRAGMENT_BASE_URL}/api")
            )
        return parse_json_response(resp, data.get("method", "request"))
    raise FragmentPageError(FragmentPageError.BAD_STATUS.format(status=429, url=f"{FRAGMENT_BASE_URL}/api"))
