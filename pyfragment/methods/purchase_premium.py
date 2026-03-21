import json
import time
from typing import TYPE_CHECKING

import httpx

from pyfragment.types import (
    ConfigurationError,
    FragmentAPIError,
    FragmentError,
    PremiumResult,
    UnexpectedError,
    UserNotFoundError,
)
from pyfragment.types.constants import DEVICE, PREMIUM_PAGE
from pyfragment.utils import (
    execute_transaction_request,
    fragment_request,
    get_account_info,
    get_fragment_hash,
    make_headers,
    process_transaction,
)

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient

HEADERS: dict[str, str] = make_headers(PREMIUM_PAGE)


async def _search_recipient(
    session: httpx.AsyncClient,
    fragment_hash: str,
    username: str,
    months: int,
) -> str:
    result = await fragment_request(
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
    await fragment_request(
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
    result = await fragment_request(
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


async def purchase_premium(client: "FragmentClient", username: str, months: int, show_sender: bool = True) -> PremiumResult:
    """Gift Telegram Premium to a user.

    Args:
        client: Authenticated :class:`FragmentClient` instance.
        username: Recipient's Telegram username (with or without ``@``).
        months: Premium duration — ``3``, ``6``, or ``12``.
        show_sender: Show your name as the gift sender. Defaults to ``True``.

    Returns:
        :class:`PremiumResult` with ``transaction_id``, ``username``, and ``months``.

    Raises:
        ConfigurationError: If ``months`` is not ``3``, ``6``, or ``12``.
        UserNotFoundError: If the user is not found on Fragment.
        FragmentAPIError: If the Fragment API returns an error.
        UnexpectedError: For any other unexpected failure.
    """
    if months not in (3, 6, 12):
        raise ConfigurationError(ConfigurationError.INVALID_MONTHS)

    try:
        fragment_hash = await get_fragment_hash(client.cookies, HEADERS, PREMIUM_PAGE, client.timeout)
        account = await get_account_info(client)

        async with httpx.AsyncClient(cookies=client.cookies, timeout=client.timeout) as session:
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
        return PremiumResult(transaction_id=tx_hash, username=username, amount=months)

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc
