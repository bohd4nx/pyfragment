import logging
import re
from typing import Any

import httpx

from app.core import HashFetchError

logger = logging.getLogger(__name__)


async def get_fragment_hash(
    cookies: dict[str, Any],
    headers: dict[str, str],
    page_url: str,
) -> str:
    # Must look like a real browser navigation — not an XHR — otherwise Fragment
    # returns JSON (no hash in it) instead of full HTML.
    page_headers = {
        k: v
        for k, v in headers.items()
        if k
        not in ("accept", "accept-encoding", "content-type", "x-requested-with", "x-aj-referer")
    }
    page_headers.update(
        {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "referer": "https://fragment.com/",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "upgrade-insecure-requests": "1",
        }
    )

    async with httpx.AsyncClient(cookies=cookies) as client:
        response = await client.get(page_url, headers=page_headers)

    if response.status_code != 200:
        raise HashFetchError(
            f"Fragment returned HTTP {response.status_code} for {page_url}. "
            "Check that your cookies are valid and not expired."
        )

    match = re.search(r"(?:https://fragment\.com)?/api\?hash=([a-f0-9]+)", response.text)
    if not match:
        raise HashFetchError(
            f"Fragment hash not found in the page source of {page_url}. "
            "The page structure may have changed or you are not logged in."
        )

    return match.group(1)
