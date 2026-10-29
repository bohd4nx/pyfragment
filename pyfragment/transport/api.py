from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable
from http import HTTPStatus
from typing import Any, cast

from curl_cffi.requests import AsyncSession, Response
from curl_cffi.requests.exceptions import RequestException

from pyfragment.constants import FRAGMENT_API_URL, MAX_API_ATTEMPTS
from pyfragment.enums import ApiError
from pyfragment.exceptions import HTTPStatusError, NetworkError, ParseError, SessionExpiredError
from pyfragment.schemas import has_error

SESSION_REJECTED_STATUSES: frozenset[int] = frozenset({HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN})


def parse_json_response(response: Response, context: str) -> dict[str, Any]:
    try:
        return cast(dict[str, Any], response.json())  # type: ignore[no-untyped-call]
    except Exception as exc:
        raise ParseError(ParseError.UNPARSEABLE.format(context=context, exc=exc)) from exc


def is_bad_hash(response: dict[str, Any]) -> bool:
    """Whether Fragment rejected the request's ``hash`` (it answers HTTP 200 with a "Bad request" error body)."""
    return has_error(response, ApiError.BAD_REQUEST)


def status_error(status: int, url: str) -> HTTPStatusError | SessionExpiredError:
    """The error for a non-200 answer: a rejected session asks for new cookies, anything else is just a bad status."""
    if status in SESSION_REJECTED_STATUSES:
        return SessionExpiredError(SessionExpiredError.REJECTED.format(status=status, url=url))
    return HTTPStatusError(status, url)


async def send(request: Awaitable[Response], url: str) -> Response:
    """Await one HTTP request; a failure to reach Fragment at all becomes a ``NetworkError``."""
    try:
        return await request
    except RequestException as exc:
        raise NetworkError(NetworkError.UNREACHABLE.format(url=url, exc=exc)) from exc


async def fragment_request(
    session: AsyncSession[Any],
    fragment_hash: str,
    headers: dict[str, str | None],
    data: dict[str, Any],
) -> dict[str, Any]:
    """POST one method call to ``/api?hash=...``, retrying HTTP 429 with jittered backoff (Fragment didn't process it)."""
    for attempt in range(1, MAX_API_ATTEMPTS + 1):
        resp = await send(
            session.post(f"{FRAGMENT_API_URL}?hash={fragment_hash}", headers=headers, data=data), FRAGMENT_API_URL
        )
        if resp.status_code == HTTPStatus.TOO_MANY_REQUESTS and attempt < MAX_API_ATTEMPTS:
            await asyncio.sleep(attempt + random.uniform(0, 0.5))
            continue
        break
    if resp.status_code != HTTPStatus.OK:
        raise status_error(resp.status_code, FRAGMENT_API_URL)
    return parse_json_response(resp, str(data.get("method", "request")))
