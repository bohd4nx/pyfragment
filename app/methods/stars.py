import json
import logging
import time

import httpx

from app.core import load_cookies
from app.core.constants import BASE_HEADERS, DEVICE, STARS_PAGE
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
    "referer": STARS_PAGE,
    "x-aj-referer": STARS_PAGE,
}


async def search_stars_recipient(
    client: httpx.AsyncClient,
    fragment_hash: str,
    cookies: dict,
    username: str,
) -> str:
    resp = await client.post(
        f"https://fragment.com/api?hash={fragment_hash}",
        headers=HEADERS,
        cookies=cookies,
        data={"query": username, "quantity": "", "method": "searchStarsRecipient"},
    )
    result = parse_json_response(resp, "searchStarsRecipient")
    recipient = result.get("found", {}).get("recipient")
    if not recipient:
        raise UserNotFoundError(
            f"Telegram user '{username}' was not found on Fragment. "
            "Make sure the username is correct and the account exists."
        )
    return recipient


async def init_buy_stars(
    client: httpx.AsyncClient,
    fragment_hash: str,
    cookies: dict,
    recipient: str,
    amount: int,
) -> str:
    resp = await client.post(
        f"https://fragment.com/api?hash={fragment_hash}",
        headers=HEADERS,
        cookies=cookies,
        data={"recipient": recipient, "quantity": amount, "method": "initBuyStarsRequest"},
    )
    result = parse_json_response(resp, "initBuyStarsRequest")
    req_id = result.get("req_id")
    if not req_id:
        raise FragmentError(
            "Fragment did not return a request ID for this Stars purchase. "
            "The session may have expired — refresh your cookies."
        )
    return req_id


async def buy_stars(username: str, amount: int) -> dict:
    if not isinstance(amount, int) or amount < 50:
        return {"success": False, "error": "Amount must be an integer >= 50 stars."}

    try:
        logger.info("Loading session cookies")
        cookies = load_cookies()

        logger.info("Fetching Fragment session hash")
        fragment_hash = await get_fragment_hash(cookies, HEADERS, STARS_PAGE)

        # logger.info("Retrieving TON wallet info")
        account = await get_account_info()

        async with httpx.AsyncClient() as client:
            logger.info("Searching recipient: %s", username)
            recipient = await search_stars_recipient(client, fragment_hash, cookies, username)

            logger.info("Initializing Stars purchase request: %s stars to %s", amount, username)
            req_id = await init_buy_stars(client, fragment_hash, cookies, recipient, amount)

            # logger.info("Requesting transaction payload (req_id=%s)", req_id)
            tx_data = {
                "account": json.dumps(account),
                "device": DEVICE,
                "transaction": 1,
                "id": req_id,
                "show_sender": 1,
                "method": "getBuyStarsLink",
            }
            transaction = await execute_transaction_request(
                client, HEADERS, cookies, account, tx_data, fragment_hash
            )

        logger.info("Broadcasting transaction to TON blockchain")
        tx_hash = await process_transaction(transaction)
        return {
            "success": True,
            "data": {
                "transaction_id": tx_hash,
                "username": username,
                "amount": amount,
                "timestamp": int(time.time()),
            },
        }

    except FragmentError as exc:
        logger.error("Stars purchase failed — %s", exc)
        return {"success": False, "error": str(exc)}
    except Exception as exc:
        logger.exception("Unexpected error during Stars purchase")
        return {"success": False, "error": f"Unexpected error: {exc}"}
