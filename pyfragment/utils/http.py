import re
from typing import Any

import httpx

from pyfragment.types import FragmentPageError, ParseError, VerificationError
from pyfragment.types.constants import DEFAULT_TIMEOUT


async def get_fragment_hash(
    cookies: dict[str, Any],
    headers: dict[str, str],
    page_url: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> str:
    """Fetch the API hash from a Fragment page.

    Fragment embeds a short-lived hash in each page's HTML that must be
    included in every subsequent API request. This function loads the page
    as a real browser navigation (not XHR) so Fragment returns full HTML.

    Args:
        cookies: Active Fragment session cookies.
        headers: Base headers for the relevant Fragment page.
        page_url: URL of the Fragment page to fetch the hash from.
        timeout: HTTP request timeout in seconds. Defaults to ``DEFAULT_TIMEOUT``.

    Returns:
        Lowercase hex hash string.

    Raises:
        FragmentPageError: If the page returns a non-200 status or the hash
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

    async with httpx.AsyncClient(cookies=cookies, timeout=timeout) as session:
        response = await session.get(page_url, headers=page_headers)

    if response.status_code != 200:
        raise FragmentPageError(FragmentPageError.BAD_STATUS.format(status=response.status_code, url=page_url))

    match = re.search(r"(?:https://fragment\.com)?/api\?hash=([a-f0-9]+)", response.text)
    if not match:
        raise FragmentPageError(FragmentPageError.NOT_FOUND.format(url=page_url))

    return match.group(1)


def parse_json_response(response: httpx.Response, context: str) -> dict[str, Any]:
    """Parse a Fragment API JSON response.

    Args:
        response: The HTTP response object.
        context: Human-readable name of the API method, used in error messages.

    Returns:
        Parsed response as a dict.

    Raises:
        ParseError: If the response body cannot be decoded as JSON.
    """
    try:
        return response.json()
    except Exception as exc:
        raise ParseError(ParseError.UNPARSEABLE.format(context=context, exc=exc)) from exc


async def fragment_post(
    session: httpx.AsyncClient,
    fragment_hash: str,
    headers: dict[str, str],
    data: dict[str, Any],
) -> dict[str, Any]:
    """POST a single request to the Fragment API.

    Builds the ``/api?hash=`` URL, sends the request, and returns the
    parsed JSON body. Use this for every API method call — search,
    init, state updates, etc.

    Args:
        session: Active httpx session with Fragment cookies.
        fragment_hash: Short-lived hash from the Fragment page HTML.
        headers: Page-specific HTTP headers.
        data: Form data payload; must include a ``"method"`` key.

    Returns:
        Parsed API response as a dict.
    """
    resp = await session.post(
        f"https://fragment.com/api?hash={fragment_hash}",
        headers=headers,
        data=data,
    )
    return parse_json_response(resp, data.get("method", "request"))


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
        ParseError: If the response cannot be parsed.
    """
    transaction = await fragment_post(session, fragment_hash, headers, tx_data)

    if transaction.get("need_verify"):
        raise VerificationError(VerificationError.KYC_REQUIRED)

    return transaction
