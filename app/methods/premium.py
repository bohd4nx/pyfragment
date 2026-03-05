import json
import logging
import time

import httpx

from app.core import load_cookies
from app.core.constants import BASE_HEADERS, DEVICE, PREMIUM_PAGE
from app.core.exceptions import FragmentError, UserNotFoundError
from app.utils import (
    execute_transaction_request,
    get_account_info,
    get_fragment_hash,
    parse_json_response,
    process_transaction,
)

logger = logging.getLogger(__name__)

# Page-specific headers
HEADERS: dict[str, str] = {
    **BASE_HEADERS,
    "referer":      PREMIUM_PAGE,
    "x-aj-referer": PREMIUM_PAGE,
}


async def search_premium_recipient(
    client: httpx.AsyncClient,
    fragment_hash: str,
    cookies: dict,
    username: str,
    months: int,
) -> str:
    resp = await client.post(
        f"https://fragment.com/api?hash={fragment_hash}",
        headers=HEADERS, cookies=cookies,
        data={"query": username, "months": months, "method": "searchPremiumGiftRecipient"},
    )
    result = parse_json_response(resp, "searchPremiumGiftRecipient")
    recipient = result.get("found", {}).get("recipient")
    if not recipient:
        raise UserNotFoundError(
            f"Telegram user '{username}' was not found on Fragment. "
            "Make sure the username is correct and the account exists."
        )
    return recipient


async def init_gift_premium(
    client: httpx.AsyncClient,
    fragment_hash: str,
    cookies: dict,
    recipient: str,
    months: int,
) -> str:
    await client.post(
        f"https://fragment.com/api?hash={fragment_hash}",
        headers=HEADERS, cookies=cookies,
        data={"mode": "new", "lv": "false", "dh": str(int(time.time())), "method": "updatePremiumState"},
    )
    resp = await client.post(
        f"https://fragment.com/api?hash={fragment_hash}",
        headers=HEADERS, cookies=cookies,
        data={"recipient": recipient, "months": months, "method": "initGiftPremiumRequest"},
    )
    result = parse_json_response(resp, "initGiftPremiumRequest")
    req_id = result.get("req_id")
    if not req_id:
        raise FragmentError(
            "Fragment did not return a request ID for this Premium purchase. "
            "The session may have expired — refresh your cookies."
        )
    return req_id


async def buy_premium(username: str, months: int) -> dict:
    if months not in (3, 6, 12):
        return {"success": False, "error": "Invalid duration. Choose 3, 6, or 12 months."}

    try:
        cookies       = load_cookies()
        fragment_hash = await get_fragment_hash(cookies, HEADERS, PREMIUM_PAGE)
        account       = await get_account_info()

        async with httpx.AsyncClient() as client:
            recipient = await search_premium_recipient(client, fragment_hash, cookies, username, months)
            req_id    = await init_gift_premium(client, fragment_hash, cookies, recipient, months)

            tx_data = {
                "account":     json.dumps(account),
                "device":      DEVICE,
                "transaction": 1,
                "id":          req_id,
                "show_sender": 1,
                "method":      "getGiftPremiumLink",
            }
            transaction = await execute_transaction_request(client, HEADERS, cookies, account, tx_data, fragment_hash)

        tx_hash = await process_transaction(transaction)
        return {
            "success": True,
            "data": {
                "transaction_id": tx_hash,
                "username":       username,
                "months":         months,
                "timestamp":      int(time.time()),
            },
        }

    except FragmentError as exc:
        logger.error("Premium purchase failed — %s", exc)
        return {"success": False, "error": str(exc)}
    except Exception as exc:
        logger.exception("Unexpected error during Premium purchase")
        return {"success": False, "error": f"Unexpected error: {exc}"}
