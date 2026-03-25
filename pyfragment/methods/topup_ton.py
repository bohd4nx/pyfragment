import json
from typing import TYPE_CHECKING

import httpx

from pyfragment.types import (
    AdsTopupResult,
    ConfigurationError,
    FragmentAPIError,
    FragmentError,
    UnexpectedError,
    UserNotFoundError,
)
from pyfragment.types.constants import ADS_TOPUP_PAGE, DEVICE
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

HEADERS: dict[str, str] = make_headers(ADS_TOPUP_PAGE)


async def _search_recipient(
    session: httpx.AsyncClient,
    fragment_hash: str,
    username: str,
) -> str:
    await fragment_request(session, fragment_hash, HEADERS, {"mode": "new", "method": "updateAdsTopupState"})
    result = await fragment_request(
        session,
        fragment_hash,
        HEADERS,
        {
            "query": username,
            "method": "searchAdsTopupRecipient",
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
    amount: int,
) -> str:
    result = await fragment_request(
        session,
        fragment_hash,
        HEADERS,
        {
            "recipient": recipient,
            "amount": amount,
            "method": "initAdsTopupRequest",
        },
    )
    req_id = result.get("req_id")
    if not req_id:
        raise FragmentAPIError(FragmentAPIError.NO_REQUEST_ID.format(context="TON topup"))
    return req_id


async def topup_ton(client: "FragmentClient", username: str, amount: int, show_sender: bool = True) -> AdsTopupResult:
    """Topup ton to recipient's Telegram balance.

    Args:
        client: Authenticated :class:`FragmentClient` instance.
        username: Recipient's Telegram username (with or without ``@``).
        amount: Amount in TON — integer from ``1`` to ``1 000 000 000``.
        show_sender: Show your name as the sender. Defaults to ``True``.

    Returns:
        :class:`AdsTopupResult` with ``transaction_id``, ``username``, and ``amount``.

    Raises:
        ConfigurationError: If ``amount`` is not an integer between 1 and 1 000 000 000.
        UserNotFoundError: If the recipient is not found on Fragment.
        FragmentAPIError: If the Fragment API returns an error.
        UnexpectedError: For any other unexpected failure.
    """
    if not isinstance(amount, int) or not (1 <= amount <= 1_000_000_000):
        raise ConfigurationError(ConfigurationError.INVALID_TON_AMOUNT)

    try:
        fragment_hash = await get_fragment_hash(client.cookies, HEADERS, ADS_TOPUP_PAGE, client.timeout)
        account = await get_account_info(client)

        async with httpx.AsyncClient(cookies=client.cookies, timeout=client.timeout) as session:
            recipient = await _search_recipient(session, fragment_hash, username)
            req_id = await _init_request(session, fragment_hash, recipient, amount)

            tx_data = {
                "account": json.dumps(account),
                "device": DEVICE,
                "transaction": 1,
                "id": req_id,
                "show_sender": int(show_sender),
                "method": "getAdsTopupLink",
            }
            transaction = await execute_transaction_request(session, HEADERS, tx_data, fragment_hash)

        tx_hash = await process_transaction(client, transaction)
        return AdsTopupResult(transaction_id=tx_hash, username=username, amount=amount)

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc
