import re
from typing import Any

import httpx

from fragmentapi.types import HashFetchError, RequestError, VerificationError


async def get_fragment_hash(
    cookies: dict[str, Any],
    headers: dict[str, str],
    page_url: str,
) -> str:
    """Fetch the API hash from a Fragment page.

    Fragment embeds a short-lived hash in each page's HTML that must be
    included in every subsequent API request. This function loads the page
    as a real browser navigation (not XHR) so Fragment returns full HTML.

    Args:
        cookies: Active Fragment session cookies.
        headers: Base headers for the relevant Fragment page.
        page_url: URL of the Fragment page to fetch the hash from.

    Returns:
        Lowercase hex hash string.

    Raises:
        HashFetchError: If the page returns a non-200 status or the hash
            is not found in the response HTML.
    """
    page_headers = {
        k: v
        for k, v in headers.items()
        if k not in ("accept", "accept-encoding", "content-type", "x-requested-with", "x-aj-referer")
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

    async with httpx.AsyncClient(cookies=cookies) as session:
        response = await session.get(page_url, headers=page_headers)

    if response.status_code != 200:
        raise HashFetchError(HashFetchError.BAD_STATUS.format(status=response.status_code, url=page_url))

    match = re.search(r"(?:https://fragment\.com)?/api\?hash=([a-f0-9]+)", response.text)
    if not match:
        raise HashFetchError(HashFetchError.NOT_FOUND.format(url=page_url))

    return match.group(1)


def parse_json_response(response: httpx.Response, context: str) -> dict[str, Any]:
    """Parse a Fragment API JSON response.

    Args:
        response: The HTTP response object.
        context: Human-readable name of the API method, used in error messages.

    Returns:
        Parsed response as a dict.

    Raises:
        RequestError: If the response body cannot be decoded as JSON.
    """
    try:
        return response.json()
    except Exception as exc:
        raise RequestError(RequestError.UNPARSEABLE.format(context=context, exc=exc)) from exc


async def execute_transaction_request(
    session: httpx.AsyncClient,
    headers: dict,
    tx_data: dict[str, Any],
    fragment_hash: str,
) -> dict[str, Any]:
    """Post a transaction request to the Fragment API.

    Args:
        session: Active httpx session with Fragment cookies.
        headers: Page-specific HTTP headers.
        tx_data: Form data payload for the API method.
        fragment_hash: Short-lived hash from the Fragment page.

    Returns:
        Parsed API response dict containing transaction data.

    Raises:
        VerificationError: If Fragment requires KYC verification.
        RequestError: If the response cannot be parsed.
    """
    url = f"https://fragment.com/api?hash={fragment_hash}"
    resp = await session.post(url, headers=headers, data=tx_data)
    transaction = parse_json_response(resp, tx_data.get("method", "transaction"))

    if transaction.get("need_verify"):
        raise VerificationError(VerificationError.KYC_REQUIRED)

    return transaction
