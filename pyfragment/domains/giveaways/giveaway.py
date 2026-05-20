from __future__ import annotations

import json
from typing import TYPE_CHECKING, get_args

from pyfragment.core.constants import DEVICE, PREMIUM_GIVEAWAY_PAGE, STARS_GIVEAWAY_PAGE
from pyfragment.domains.payments import parse_required_payment_amount
from pyfragment.domains.wallet.info import get_account_info
from pyfragment.domains.wallet.transaction import process_transaction
from pyfragment.exceptions import (
    ConfigurationError,
    FragmentAPIError,
    FragmentError,
    UnexpectedError,
    UserNotFoundError,
    VerificationError,
)
from pyfragment.models.enums import PaymentMethod
from pyfragment.models.giveaways import PremiumGiveawayResult, StarsGiveawayResult

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


async def giveaway_stars(
    client: FragmentClient,
    channel: str,
    winners: int,
    amount: int,
    payment_method: PaymentMethod = "ton",
) -> StarsGiveawayResult:
    if not isinstance(winners, int) or not (1 <= winners <= 5):
        raise ConfigurationError(ConfigurationError.INVALID_WINNERS_STARS)
    if not isinstance(amount, int) or not (500 <= amount <= 1_000_000):
        raise ConfigurationError(ConfigurationError.INVALID_STARS_PER_WINNER)
    if payment_method not in get_args(PaymentMethod):
        raise ConfigurationError(
            ConfigurationError.INVALID_PAYMENT_METHOD.format(
                method=payment_method,
                supported=", ".join(sorted(get_args(PaymentMethod))),
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
        required_payment_amount = parse_required_payment_amount(result)
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

        tx_hash = await process_transaction(
            client,
            transaction,
            payment_method=payment_method,
            required_payment_amount=required_payment_amount,
        )
        return StarsGiveawayResult(transaction_id=tx_hash, channel=channel, winners=winners, amount=amount)

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc


async def giveaway_premium(
    client: FragmentClient,
    channel: str,
    winners: int,
    months: int = 3,
    payment_method: PaymentMethod = "ton",
) -> PremiumGiveawayResult:
    if not isinstance(winners, int) or not (1 <= winners <= 24_000):
        raise ConfigurationError(ConfigurationError.INVALID_WINNERS_PREMIUM)
    if months not in (3, 6, 12):
        raise ConfigurationError(ConfigurationError.INVALID_MONTHS)
    if payment_method not in get_args(PaymentMethod):
        raise ConfigurationError(
            ConfigurationError.INVALID_PAYMENT_METHOD.format(
                method=payment_method,
                supported=", ".join(sorted(get_args(PaymentMethod))),
            )
        )

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
            {
                "recipient": recipient,
                "quantity": str(winners),
                "months": str(months),
                "payment_method": payment_method,
            },
            page_url=PREMIUM_GIVEAWAY_PAGE,
        )
        required_payment_amount = parse_required_payment_amount(result)
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

        tx_hash = await process_transaction(
            client,
            transaction,
            payment_method=payment_method,
            required_payment_amount=required_payment_amount,
        )
        return PremiumGiveawayResult(transaction_id=tx_hash, channel=channel, winners=winners, amount=months)

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc
