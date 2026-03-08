import json
import logging
import time

import httpx

from app.core import (
    BASE_HEADERS,
    DEVICE,
    PREMIUM_PAGE,
    FragmentError,
    UserNotFoundError,
    load_cookies,
)
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
    "referer": PREMIUM_PAGE,
    "x-aj-referer": PREMIUM_PAGE,
}


async def search_premium_recipient(
    client: httpx.AsyncClient,
    fragment_hash: str,
    username: str,
    months: int,
) -> str:
    resp = await client.post(
        f"https://fragment.com/api?hash={fragment_hash}",
        headers=HEADERS,
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
    recipient: str,
    months: int,
) -> str:
    await client.post(
        f"https://fragment.com/api?hash={fragment_hash}",
        headers=HEADERS,
        data={
            "mode": "new",
            "lv": "false",
            "dh": str(int(time.time())),
            "method": "updatePremiumState",
        },
    )
    resp = await client.post(
        f"https://fragment.com/api?hash={fragment_hash}",
        headers=HEADERS,
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
        logger.info("Loading session cookies")
        cookies = load_cookies()

        logger.info("Fetching Fragment session hash")
        fragment_hash = await get_fragment_hash(cookies, HEADERS, PREMIUM_PAGE)

        # logger.info("Retrieving TON wallet info")
        account = await get_account_info()

        async with httpx.AsyncClient(cookies=cookies) as client:
            logger.info("Searching recipient: %s", username)
            recipient = await search_premium_recipient(client, fragment_hash, username, months)

            logger.info("Initializing Premium gift request: %s months to %s", months, username)
            req_id = await init_gift_premium(client, fragment_hash, recipient, months)

            # logger.info("Requesting transaction payload (req_id=%s)", req_id)
            tx_data = {
                "account": json.dumps(account),
                "device": DEVICE,
                "transaction": 1,
                "id": req_id,
                "show_sender": 1,
                "method": "getGiftPremiumLink",
            }
            transaction = await execute_transaction_request(
                client, HEADERS, account, tx_data, fragment_hash
            )

        logger.info("Broadcasting transaction to TON blockchain")
        tx_hash = await process_transaction(transaction)
        logger.info(
            "Premium purchase successful: %s months -> %s | tx: %s", months, username, tx_hash
        )
        return {
            "success": True,
            "data": {
                "transaction_id": tx_hash,
                "username": username,
                "months": months,
                "timestamp": int(time.time()),
            },
        }

    except FragmentError as exc:
        logger.error("Premium purchase failed — %s", exc)
        return {"success": False, "error": str(exc)}
    except Exception as exc:
        logger.exception("Unexpected error during Premium purchase")
        return {"success": False, "error": f"Unexpected error: {exc}"}
