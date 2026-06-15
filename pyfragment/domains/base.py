from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import httpx

from pyfragment.core.constants import BASE_HEADERS
from pyfragment.core.transport import fragment_request, get_fragment_hash

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient

logger = logging.getLogger(__name__)


async def raw_api_call(
    cookies: dict[str, Any],
    timeout: float,
    method: str,
    data: dict[str, Any] | None,
    page_url: str,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    base = headers if headers is not None else BASE_HEADERS
    payload = {"method": method, **(data or {})}
    call_headers = {**base, "referer": page_url, "x-aj-referer": page_url}
    logger.debug("Starting Fragment API call '%s' on %s", method, page_url)
    try:
        async with httpx.AsyncClient(cookies=cookies, timeout=timeout) as session:
            fragment_hash = await get_fragment_hash(cookies, call_headers, page_url, timeout)
            response = await fragment_request(session, fragment_hash, call_headers, payload)
            logger.debug("Completed Fragment API call '%s' with response keys: %s", method, sorted(response.keys()))
            return response
    except Exception:
        logger.exception("Failed to call Fragment API method '%s' on %s", method, page_url)
        raise


class BaseService:
    def __init__(self, client: FragmentClient) -> None:
        self._client = client
