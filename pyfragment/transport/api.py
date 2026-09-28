from __future__ import annotations

import asyncio
import random
from http import HTTPStatus
from typing import Any, cast

from curl_cffi.requests import AsyncSession, Response

from pyfragment.core.constants import FRAGMENT_API_URL, MAX_API_ATTEMPTS
from pyfragment.enums import ApiError
from pyfragment.exceptions import FragmentPageError, ParseError
from pyfragment.schemas import has_error


def parse_json_response(response: Response, context: str) -> dict[str, Any]:
    try:
        return cast(dict[str, Any], response.json())  # type: ignore[no-untyped-call]
    except Exception as exc:
        raise ParseError(ParseError.UNPARSEABLE.format(context=context, exc=exc)) from exc


def is_bad_hash(response: dict[str, Any]) -> bool:
    """Whether Fragment rejected the request's ``hash`` (it answers HTTP 200 with a "Bad request" error body)."""
    return has_error(response, ApiError.BAD_REQUEST)


async def fragment_request(
    session: AsyncSession[Any],
    fragment_hash: str,
    headers: dict[str, str | None],
    data: dict[str, Any],
) -> dict[str, Any]:
    """POST one method call to ``/api?hash=...``, retrying HTTP 429 with jittered backoff."""
    for attempt in range(MAX_API_ATTEMPTS):
        resp = await session.post(f"{FRAGMENT_API_URL}?hash={fragment_hash}", headers=headers, data=data)
        if resp.status_code == HTTPStatus.TOO_MANY_REQUESTS and attempt < MAX_API_ATTEMPTS - 1:
            await asyncio.sleep(1 + attempt + random.uniform(0, 0.5))
            continue
        if resp.status_code != HTTPStatus.OK:
            raise FragmentPageError(FragmentPageError.BAD_STATUS.format(status=resp.status_code, url=FRAGMENT_API_URL))
        return parse_json_response(resp, data.get("method", "request"))
    raise FragmentPageError(
        FragmentPageError.BAD_STATUS.format(status=HTTPStatus.TOO_MANY_REQUESTS.value, url=FRAGMENT_API_URL)
    )
