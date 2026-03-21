import json
from typing import TYPE_CHECKING

import httpx

from pyfragment.types import (
    ConfigurationError,
    FragmentAPIError,
    FragmentError,
    UnexpectedError,
    UserNotFoundError,
)
from pyfragment.types.constants import DEVICE, PREMIUM_GIVEAWAY_PAGE
from pyfragment.types.results import PremiumGiveawayResult
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

HEADERS: dict[str, str] = make_headers(PREMIUM_GIVEAWAY_PAGE)


async def _search_recipient(
    session: httpx.AsyncClient,
    fragment_hash: str,
    channel: str,
    winners: int,
    months: int,
) -> str:
    result = await fragment_request(
        session,
        fragment_hash,
        HEADERS,
        {
            "query": channel,
            "quantity": winners,
            "months": months,
            "method": "searchPremiumGiveawayRecipient",
        },
    )
    recipient = result.get("found", {}).get("recipient")
    if not recipient:
        raise UserNotFoundError(UserNotFoundError.NOT_FOUND.format(username=channel))
    return recipient


async def _init_request(
    session: httpx.AsyncClient,
    fragment_hash: str,
    recipient: str,
    winners: int,
    months: int,
) -> str:
    result = await fragment_request(
        session,
        fragment_hash,
        HEADERS,
        {
            "recipient": recipient,
            "quantity": str(winners),
            "months": str(months),
            "method": "initGiveawayPremiumRequest",
        },
    )
    req_id = result.get("req_id")
    if not req_id:
        raise FragmentAPIError(FragmentAPIError.NO_REQUEST_ID.format(context="Premium giveaway"))
    return req_id


async def giveaway_premium(
    client: "FragmentClient",
    channel: str,
    winners: int,
    months: int = 3,
) -> PremiumGiveawayResult:
    """Run a Telegram Premium giveaway for a channel.

    Args:
        client: Authenticated :class:`FragmentClient` instance.
        channel: Channel username (with or without ``@``).
        winners: Number of winners — integer from ``1`` to ``24 000``.
        months: Premium duration per winner — ``3``, ``6``, or ``12``. Defaults to ``3``.

    Returns:
        :class:`PremiumGiveawayResult` with ``transaction_id``, ``channel``,
        ``winners``, and ``months``.

    Raises:
        ConfigurationError: If ``winners`` is not 1–24 000 or ``months`` is not 3, 6, or 12.
        UserNotFoundError: If the channel is not found on Fragment.
        FragmentAPIError: If the Fragment API returns an error.
        UnexpectedError: For any other unexpected failure.
    """
    if not isinstance(winners, int) or not (1 <= winners <= 24_000):
        raise ConfigurationError(ConfigurationError.INVALID_WINNERS_PREMIUM)
    if months not in (3, 6, 12):
        raise ConfigurationError(ConfigurationError.INVALID_MONTHS)

    try:
        fragment_hash = await get_fragment_hash(client.cookies, HEADERS, PREMIUM_GIVEAWAY_PAGE, client.timeout)
        account = await get_account_info(client)

        async with httpx.AsyncClient(cookies=client.cookies, timeout=client.timeout) as session:
            recipient = await _search_recipient(session, fragment_hash, channel, winners, months)
            req_id = await _init_request(session, fragment_hash, recipient, winners, months)

            tx_data = {
                "account": json.dumps(account),
                "device": DEVICE,
                "transaction": 1,
                "id": req_id,
                "method": "getGiveawayPremiumLink",
            }
            transaction = await execute_transaction_request(session, HEADERS, tx_data, fragment_hash)

        tx_hash = await process_transaction(client, transaction)
        return PremiumGiveawayResult(
            transaction_id=tx_hash,
            channel=channel,
            winners=winners,
            amount=months,
        )

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc
