import json
import time
from typing import TYPE_CHECKING

import httpx

from pyfragment.types import (
    BASE_HEADERS,
    DEVICE,
    PREMIUM_PAGE,
    ConfigurationError,
    FragmentAPIError,
    FragmentError,
    PremiumResult,
    UnexpectedError,
    UserNotFoundError,
)
from pyfragment.utils import (
    execute_transaction_request,
    fragment_post,
    get_account_info,
    get_fragment_hash,
    process_transaction,
)

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient

# Page-specific headers
HEADERS: dict[str, str] = {
    **BASE_HEADERS,
    "referer": PREMIUM_PAGE,
    "x-aj-referer": PREMIUM_PAGE,
}


async def _search_recipient(
    session: httpx.AsyncClient,
    fragment_hash: str,
    username: str,
    months: int,
) -> str:
    result = await fragment_post(
        session,
        fragment_hash,
        HEADERS,
        {
            "query": username,
            "months": months,
            "method": "searchPremiumGiftRecipient",
        },
    )
    recipient = result.get("found", {}).get("recipient")
    if not recipient:
        raise UserNotFoundError(UserNotFoundError.NOT_FOUND.format(username=username))
    return recipient


async def _init_request(
    session: httpx.AsyncClient,
    fragment_hash: str,
    recipient: str,
    months: int,
) -> str:
    await fragment_post(
        session,
        fragment_hash,
        HEADERS,
        {
            "mode": "new",
            "lv": "false",
            "dh": str(int(time.time())),
            "method": "updatePremiumState",
        },
    )
    result = await fragment_post(
        session,
        fragment_hash,
        HEADERS,
        {
            "recipient": recipient,
            "months": months,
            "method": "initGiftPremiumRequest",
        },
    )
    req_id = result.get("req_id")
    if not req_id:
        raise FragmentAPIError(FragmentAPIError.NO_REQUEST_ID.format(context="Premium purchase"))
    return req_id


async def gift_premium(client: "FragmentClient", username: str, months: int, show_sender: bool = True) -> PremiumResult:
    if months not in (3, 6, 12):
        raise ConfigurationError(ConfigurationError.INVALID_MONTHS)

    try:
        fragment_hash = await get_fragment_hash(client.cookies, HEADERS, PREMIUM_PAGE)
        account = await get_account_info(client)

        async with httpx.AsyncClient(cookies=client.cookies) as session:
            recipient = await _search_recipient(session, fragment_hash, username, months)
            req_id = await _init_request(session, fragment_hash, recipient, months)

            tx_data = {
                "account": json.dumps(account),
                "device": DEVICE,
                "transaction": 1,
                "id": req_id,
                "show_sender": int(show_sender),
                "method": "getGiftPremiumLink",
            }
            transaction = await execute_transaction_request(session, HEADERS, tx_data, fragment_hash)

        tx_hash = await process_transaction(client, transaction)
        return PremiumResult(transaction_id=tx_hash, username=username, months=months)

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc
