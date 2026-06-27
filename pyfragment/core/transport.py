from __future__ import annotations

import asyncio
import random
import re
from typing import Any, cast

import httpx

from pyfragment.core.constants import DEFAULT_TIMEOUT, FRAGMENT_BASE_URL
from pyfragment.exceptions import FragmentPageError, ParseError


async def get_fragment_hash(
    cookies: dict[str, Any],
    headers: dict[str, str],
    page_url: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> str:
    page_headers = {
        k: v
        for k, v in headers.items()
        if k not in ("accept", "accept-encoding", "content-type", "x-requested-with", "x-aj-referer")
    }
    page_headers.update(
        {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "referer": f"{FRAGMENT_BASE_URL}/",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "upgrade-insecure-requests": "1",
        }
    )

    async with httpx.AsyncClient(cookies=cookies, timeout=timeout) as session:
        response = await session.get(page_url, headers=page_headers)

    if response.status_code != 200:
        raise FragmentPageError(FragmentPageError.BAD_STATUS.format(status=response.status_code, url=page_url))

    match = re.search(r"(?:https://fragment\.com)?/api\?hash=([a-f0-9]+)", response.text)
    if not match:
        raise FragmentPageError(FragmentPageError.NOT_FOUND.format(url=page_url))

    return match.group(1)


def parse_json_response(response: httpx.Response, context: str) -> dict[str, Any]:
    try:
        return cast(dict[str, Any], response.json())
    except Exception as exc:
        raise ParseError(ParseError.UNPARSEABLE.format(context=context, exc=exc)) from exc


async def fragment_request(
    session: httpx.AsyncClient,
    fragment_hash: str,
    headers: dict[str, str],
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
