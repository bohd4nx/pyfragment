from __future__ import annotations

import json
from typing import TYPE_CHECKING

from pyfragment.types import (
    ConfigurationError,
    FragmentAPIError,
    FragmentError,
    StarsGiveawayResult,
    UnexpectedError,
    UserNotFoundError,
    VerificationError,
)
from pyfragment.types.constants import DEVICE, STARS_GIVEAWAY_PAGE, SUPPORTED_PAYMENT_METHODS, PaymentMethod
from pyfragment.utils import get_account_info, process_transaction

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


async def giveaway_stars(
    client: FragmentClient,
    channel: str,
    winners: int,
    amount: int,
    payment_method: PaymentMethod = "ton",
) -> StarsGiveawayResult:
    """Run a Telegram Stars giveaway for a channel.

    Args:
        client: Authenticated :class:`FragmentClient` instance.
        channel: Channel identifier — ``@channel``, ``channel``, or ``https://t.me/channel``.
        winners: Number of winners — integer from ``1`` to ``5``.
        amount: Stars each winner receives — integer from ``500`` to ``1 000 000``.
        payment_method: Payment currency — ``"ton"`` (default) or ``"usdt_ton"``.

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
    if payment_method not in SUPPORTED_PAYMENT_METHODS:
        raise ConfigurationError(
            ConfigurationError.INVALID_PAYMENT_METHOD.format(
                method=payment_method,
                supported=", ".join(sorted(SUPPORTED_PAYMENT_METHODS)),
            )
        )

    try:
        result = await client.call("searchStarsGiveawayRecipient", {"query": channel}, page_url=STARS_GIVEAWAY_PAGE)
        recipient = result.get("found", {}).get("recipient")
        if not recipient:
            raise UserNotFoundError(UserNotFoundError.NOT_FOUND.format(username=channel))

        result = await client.call(
            "initGiveawayStarsRequest",
            {
                "recipient": recipient,
                "quantity": str(winners),
                "stars": str(amount),
                "payment_method": payment_method,
            },
            page_url=STARS_GIVEAWAY_PAGE,
        )
        req_id = result.get("req_id")
        if not req_id:
            raise FragmentAPIError(FragmentAPIError.NO_REQUEST_ID.format(context="Stars giveaway"))

        account = await get_account_info(client)
        transaction = await client.call(
            "getGiveawayStarsLink",
            {
                "account": json.dumps(account),
                "device": DEVICE,
                "transaction": 1,
                "id": req_id,
            },
            page_url=STARS_GIVEAWAY_PAGE,
        )
        if transaction.get("need_verify"):
            raise VerificationError(VerificationError.KYC_REQUIRED)

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
