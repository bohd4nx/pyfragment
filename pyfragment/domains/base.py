from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyfragment.core.constants import BASE_HEADERS
from pyfragment.transport import FragmentTransport

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


async def raw_api_call(
    cookies: dict[str, Any],
    timeout: float,
    method: str,
    data: dict[str, Any] | None,
    page_url: str,
    headers: dict[str, str | None] | None = None,
) -> dict[str, Any]:
    """One-shot Fragment API call on a throwaway session, for use without a ``FragmentClient``."""
    transport = FragmentTransport(cookies, timeout, headers if headers is not None else dict(BASE_HEADERS))
    try:
        return await transport.call(method, data, page_url)
    finally:
        await transport.aclose()


class BaseService:
    def __init__(self, client: FragmentClient) -> None:
        self._client = client
