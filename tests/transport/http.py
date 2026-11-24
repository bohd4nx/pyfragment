"""A scripted stand-in for the curl_cffi session: tests queue what each GET/POST answers and read back what was sent."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

from curl_cffi.requests import AsyncSession, Response

HASH = "abc123def456"
LOGGED_IN_PAGE = r'<script>var s = {"logged_in": true}; ajInit("\/api?hash=' + HASH + r'");</script>'
LOGGED_OUT_PAGE = r'<script src="\/api?hash=' + HASH + r'"></script><html>main page</html>'


def reply(status: int = 200, payload: Any = None, text: str = "") -> MagicMock:
    response = MagicMock(spec=Response)
    response.status_code = status
    response.json.return_value = {} if payload is None else payload
    response.text = text
    return response


def session(*, post: list[Any] | None = None, get: list[Any] | None = None) -> AsyncMock:
    """Each queued item is a response, or an exception to raise."""
    fake = AsyncMock(spec=AsyncSession)
    fake.post = AsyncMock(side_effect=post or [])
    fake.get = AsyncMock(side_effect=get or [])
    return fake
