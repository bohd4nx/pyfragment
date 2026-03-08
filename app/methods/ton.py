import json
import logging
import time

import httpx

from app.core import ADS_PAGE, BASE_HEADERS, DEVICE, FragmentError, UserNotFoundError, load_cookies
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
    "referer": ADS_PAGE,
    "x-aj-referer": ADS_PAGE,
}


async def search_ads_recipient(
    client: httpx.AsyncClient,
    fragment_hash: str,
    username: str,
) -> str:
    await client.post(
        f"https://fragment.com/api?hash={fragment_hash}",
        headers=HEADERS,
        data={"mode": "new", "method": "updateAdsTopupState"},
    )
    resp = await client.post(
        f"https://fragment.com/api?hash={fragment_hash}",
        headers=HEADERS,
        data={"query": username, "method": "searchAdsTopupRecipient"},
    )
    result = parse_json_response(resp, "searchAdsTopupRecipient")
    recipient = result.get("found", {}).get("recipient")
    if not recipient:
        raise UserNotFoundError(
            f"Telegram user '{username}' was not found on Fragment. "
            "Make sure the username is correct and the account exists."
        )
    return recipient


async def init_ads_topup(
    client: httpx.AsyncClient,
    fragment_hash: str,
    recipient: str,
    amount: int,
) -> str:
    resp = await client.post(
        f"https://fragment.com/api?hash={fragment_hash}",
        headers=HEADERS,
        data={"recipient": recipient, "amount": amount, "method": "initAdsTopupRequest"},
    )
    result = parse_json_response(resp, "initAdsTopupRequest")
    req_id = result.get("req_id")
    if not req_id:
        raise FragmentError(
            "Fragment did not return a request ID for this TON topup. "
            "The session may have expired — refresh your cookies."
        )
    return req_id


async def topup_ton(username: str, amount: int) -> dict:
    if not isinstance(amount, int) or amount < 1:
        return {"success": False, "error": "Amount must be an integer >= 1 TON."}

    try:
        logger.info("Loading session cookies")
        cookies = load_cookies()

        logger.info("Fetching Fragment session hash")
        fragment_hash = await get_fragment_hash(cookies, HEADERS, ADS_PAGE)

        # logger.info("Retrieving TON wallet info")
        account = await get_account_info()

        async with httpx.AsyncClient(cookies=cookies) as client:
            logger.info("Searching recipient: %s", username)
            recipient = await search_ads_recipient(client, fragment_hash, username)

            logger.info("Initializing topup request: %s TON to %s", amount, username)
            req_id = await init_ads_topup(client, fragment_hash, recipient, amount)

            # logger.info("Requesting transaction payload (req_id=%s)", req_id)
            tx_data = {
                "account": json.dumps(account),
                "device": DEVICE,
                "transaction": 1,
                "id": req_id,
                "show_sender": 1,
                "method": "getAdsTopupLink",
            }
            transaction = await execute_transaction_request(
                client, HEADERS, account, tx_data, fragment_hash
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
        logger.error("TON topup failed — %s", exc)
        return {"success": False, "error": str(exc)}
    except Exception as exc:
        logger.exception("Unexpected error during TON topup")
        return {"success": False, "error": f"Unexpected error: {exc}"}
