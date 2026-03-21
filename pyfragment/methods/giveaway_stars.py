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
from pyfragment.types.constants import BASE_HEADERS, DEVICE, STARS_GIVEAWAY_PAGE
from pyfragment.types.results import StarsGiveawayResult
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
    "referer": STARS_GIVEAWAY_PAGE,
    "x-aj-referer": STARS_GIVEAWAY_PAGE,
}


async def _search_recipient(
    session: httpx.AsyncClient,
    fragment_hash: str,
    channel: str,
) -> str:
    result = await fragment_post(
        session,
        fragment_hash,
        HEADERS,
        {
            "query": channel,
            "method": "searchStarsGiveawayRecipient",
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
    amount: int,
) -> str:
    result = await fragment_post(
        session,
        fragment_hash,
        HEADERS,
        {
            "recipient": recipient,
            "quantity": str(winners),
            "stars": str(amount),
            "method": "initGiveawayStarsRequest",
        },
    )
    req_id = result.get("req_id")
    if not req_id:
        raise FragmentAPIError(FragmentAPIError.NO_REQUEST_ID.format(context="Stars giveaway"))
    return req_id


async def giveaway_stars(
    client: "FragmentClient",
    channel: str,
    winners: int,
    amount: int,
) -> StarsGiveawayResult:
    """Run a Telegram Stars giveaway for a channel.

    Args:
        client: Authenticated :class:`FragmentClient` instance.
        channel: Channel username (with or without ``@``).
        winners: Number of winners — integer from ``1`` to ``5``.
        amount: Stars each winner receives — integer from ``500`` to ``1 000 000``.

    Returns:
        :class:`StarsGiveawayResult` with ``transaction_id``, ``channel``,
        ``winners``, and ``amount``.

    Raises:
        ConfigurationError: If ``winners`` is not 1–5 or ``amount`` is not 500–1 000 000.
        UserNotFoundError: If the channel is not found on Fragment.
        FragmentAPIError: If the Fragment API returns an error.
        UnexpectedError: For any other unexpected failure.
    """
    if not isinstance(winners, int) or not (1 <= winners <= 5):
        raise ConfigurationError(ConfigurationError.INVALID_WINNERS_STARS)
    if not isinstance(amount, int) or not (500 <= amount <= 1_000_000):
        raise ConfigurationError(ConfigurationError.INVALID_STARS_PER_WINNER)

    try:
        fragment_hash = await get_fragment_hash(client.cookies, HEADERS, STARS_GIVEAWAY_PAGE, client.timeout)
        account = await get_account_info(client)

        async with httpx.AsyncClient(cookies=client.cookies, timeout=client.timeout) as session:
            recipient = await _search_recipient(session, fragment_hash, channel)
            req_id = await _init_request(session, fragment_hash, recipient, winners, amount)

            tx_data = {
                "account": json.dumps(account),
                "device": DEVICE,
                "transaction": 1,
                "id": req_id,
                "method": "getGiveawayStarsLink",
            }
            transaction = await execute_transaction_request(session, HEADERS, tx_data, fragment_hash)

        tx_hash = await process_transaction(client, transaction)
        return StarsGiveawayResult(
            transaction_id=tx_hash,
            channel=channel,
            winners=winners,
            amount=amount,
        )

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc
