import logging
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)


async def get_fragment_hash(
        cookies: dict[str, Any],
        headers: dict[str, str],
        page_url: str,
) -> str | None:
    request_headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "accept-language": headers.get("accept-language") or headers.get("Accept-Language", "en-US,en;q=0.9"),
        "user-agent": headers.get("user-agent") or headers.get("User-Agent", ""),
        "referer": "https://fragment.com/",
    }

    async with httpx.AsyncClient(cookies=cookies) as client:
        response = await client.get(page_url, headers=request_headers)

    if response.status_code != 200:
        logger.error("Failed to fetch Fragment page for hash: %s", response.status_code)
        return None

    text = response.text
    match = re.search(r"(?:https://fragment\.com)?/api\?hash=([a-f0-9]+)", text)
    if match:
        return match.group(1)

    logger.error("Failed to extract Fragment hash from page")
    return None
