import logging
import re
from typing import Any

import httpx

from app.core.exceptions import HashFetchError

logger = logging.getLogger(__name__)


async def get_fragment_hash(
        cookies: dict[str, Any],
        headers: dict[str, str],
        page_url: str,
) -> str:
    page_headers = {
        **headers,
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "referer": "https://fragment.com/",
    }

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
