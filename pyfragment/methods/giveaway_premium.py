import json
from typing import TYPE_CHECKING

from pyfragment.types import (
    ConfigurationError,
    FragmentAPIError,
    FragmentError,
    PremiumGiveawayResult,
    UnexpectedError,
    UserNotFoundError,
    VerificationError,
)
from pyfragment.types.constants import DEVICE, PREMIUM_GIVEAWAY_PAGE
from pyfragment.utils import get_account_info, process_transaction

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


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
        ``winners``, and ``amount``.

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
        result = await client.call(
            "searchPremiumGiveawayRecipient",
            {"query": channel, "quantity": winners, "months": months},
            page_url=PREMIUM_GIVEAWAY_PAGE,
        )
        recipient = result.get("found", {}).get("recipient")
        if not recipient:
            raise UserNotFoundError(UserNotFoundError.NOT_FOUND.format(username=channel))

        result = await client.call(
            "initGiveawayPremiumRequest",
            {"recipient": recipient, "quantity": str(winners), "months": str(months)},
            page_url=PREMIUM_GIVEAWAY_PAGE,
        )
        req_id = result.get("req_id")
        if not req_id:
            raise FragmentAPIError(FragmentAPIError.NO_REQUEST_ID.format(context="Premium giveaway"))

        account = await get_account_info(client)
        transaction = await client.call(
            "getGiveawayPremiumLink",
            {
                "account": json.dumps(account),
                "device": DEVICE,
                "transaction": 1,
                "id": req_id,
            },
            page_url=PREMIUM_GIVEAWAY_PAGE,
        )
        if transaction.get("need_verify"):
            raise VerificationError(VerificationError.KYC_REQUIRED)

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
