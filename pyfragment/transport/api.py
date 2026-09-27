from __future__ import annotations

import asyncio
import random
from typing import Any, cast

from curl_cffi.requests import AsyncSession, Response

from pyfragment.core.constants import FRAGMENT_BASE_URL
from pyfragment.exceptions import FragmentPageError, ParseError

API_URL: str = f"{FRAGMENT_BASE_URL}/api"

# Fragment answers HTTP 200 with this error body when the `hash` query parameter is unknown or stale.
BAD_HASH_ERROR: str = "Bad request"

MAX_ATTEMPTS: int = 3


def parse_json_response(response: Response, context: str) -> dict[str, Any]:
    try:
        return cast(dict[str, Any], response.json())  # type: ignore[no-untyped-call]
    except Exception as exc:
        raise ParseError(ParseError.UNPARSEABLE.format(context=context, exc=exc)) from exc


def is_bad_hash(response: dict[str, Any]) -> bool:
    return response.get("error") == BAD_HASH_ERROR


async def fragment_request(
    session: AsyncSession[Any],
    fragment_hash: str,
    headers: dict[str, str | None],
    data: dict[str, Any],
) -> dict[str, Any]:
    """POST one method call to ``/api?hash=...``, retrying HTTP 429 with jittered backoff."""
    for attempt in range(MAX_ATTEMPTS):
        resp = await session.post(f"{API_URL}?hash={fragment_hash}", headers=headers, data=data)
        if resp.status_code == 429 and attempt < MAX_ATTEMPTS - 1:
            await asyncio.sleep(1 + attempt + random.uniform(0, 0.5))
            continue
        if resp.status_code != 200:
            raise FragmentPageError(FragmentPageError.BAD_STATUS.format(status=resp.status_code, url=API_URL))
        return parse_json_response(resp, data.get("method", "request"))
    raise FragmentPageError(FragmentPageError.BAD_STATUS.format(status=429, url=API_URL))
