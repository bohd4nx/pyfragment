import json
from typing import TYPE_CHECKING

import httpx

from fragmentapi.types import (
    BASE_HEADERS,
    DEVICE,
    STARS_PAGE,
    ConfigError,
    FragmentAPIError,
    FragmentError,
    StarsResult,
    UnexpectedError,
    UserNotFoundError,
)
from fragmentapi.utils import (
    execute_transaction_request,
    get_account_info,
    get_fragment_hash,
    parse_json_response,
    process_transaction,
)

if TYPE_CHECKING:
    from fragmentapi.client import FragmentClient

# Page-specific headers
HEADERS: dict[str, str] = {
    **BASE_HEADERS,
    "referer": STARS_PAGE,
    "x-aj-referer": STARS_PAGE,
}


async def _search_recipient(
    session: httpx.AsyncClient,
    fragment_hash: str,
    username: str,
) -> str:
    resp = await session.post(
        f"https://fragment.com/api?hash={fragment_hash}",
        headers=HEADERS,
        data={"query": username, "quantity": "", "method": "searchStarsRecipient"},
    )
    result = parse_json_response(resp, "searchStarsRecipient")
    recipient = result.get("found", {}).get("recipient")
    if not recipient:
        raise UserNotFoundError(UserNotFoundError.NOT_FOUND.format(username=username))
    return recipient


async def _init_request(
    session: httpx.AsyncClient,
    fragment_hash: str,
    recipient: str,
    amount: int,
) -> str:
    resp = await session.post(
        f"https://fragment.com/api?hash={fragment_hash}",
        headers=HEADERS,
        data={
            "recipient": recipient,
            "quantity": amount,
            "method": "initBuyStarsRequest",
        },
    )
    result = parse_json_response(resp, "initBuyStarsRequest")
    req_id = result.get("req_id")
    if not req_id:
        raise FragmentAPIError(FragmentAPIError.NO_REQUEST_ID.format(context="Stars purchase"))
    return req_id


async def gift_stars(client: "FragmentClient", username: str, amount: int, show_sender: bool = True) -> StarsResult:
    if not isinstance(amount, int) or not (50 <= amount <= 1_000_000):
        raise ConfigError(ConfigError.INVALID_STARS_AMOUNT)

    try:
        fragment_hash = await get_fragment_hash(client.cookies, HEADERS, STARS_PAGE)
        account = await get_account_info(client)

        async with httpx.AsyncClient(cookies=client.cookies) as session:
            recipient = await _search_recipient(session, fragment_hash, username)
            req_id = await _init_request(session, fragment_hash, recipient, amount)

            tx_data = {
                "account": json.dumps(account),
                "device": DEVICE,
                "transaction": 1,
                "id": req_id,
                "show_sender": int(show_sender),
                "method": "getBuyStarsLink",
            }
            transaction = await execute_transaction_request(session, HEADERS, tx_data, fragment_hash)

        tx_hash = await process_transaction(client, transaction)
        return StarsResult(transaction_id=tx_hash, username=username, stars=amount)

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc
