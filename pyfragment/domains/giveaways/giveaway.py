from __future__ import annotations

import json
import logging
import random
from typing import TYPE_CHECKING

from pyfragment.core.constants import (
    DEVICE_INFO,
    PREMIUM_GIVEAWAY_PAGE,
    PREMIUM_MONTHS_VALID,
    PREMIUM_WINNERS_MAX,
    PREMIUM_WINNERS_MIN,
    STARS_GIVEAWAY_MAX,
    STARS_GIVEAWAY_MIN,
    STARS_GIVEAWAY_PAGE,
    STARS_WINNERS_MAX,
    STARS_WINNERS_MIN,
)
from pyfragment.domains.payments import parse_required_payment_amount
from pyfragment.domains.tonapi.account import get_account_info
from pyfragment.domains.tonapi.transaction import process_transaction
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


logger = logging.getLogger(__name__)


def _state_nonce() -> str:
    # Fragment expects a pseudo-random nonce-like dh value in giveaway state updates.
    return str(random.randint(100_000_000, 2_147_483_647))


async def giveaway_stars(
    client: FragmentClient,
    channel: str,
    winners: int,
    amount: int,
    payment_method: PaymentMethod = PaymentMethod.TON,
) -> StarsGiveawayResult:
    if not isinstance(winners, int) or not (STARS_WINNERS_MIN <= winners <= STARS_WINNERS_MAX):
        raise ConfigurationError(ConfigurationError.INVALID_WINNERS_STARS)
    if not isinstance(amount, int) or not (STARS_GIVEAWAY_MIN <= amount <= STARS_GIVEAWAY_MAX):
        raise ConfigurationError(ConfigurationError.INVALID_STARS_PER_WINNER)
    if not any(payment_method == m for m in PaymentMethod):
        raise ConfigurationError(
            ConfigurationError.INVALID_PAYMENT_METHOD.format(
                method=payment_method,
                supported=", ".join(sorted(m.value for m in PaymentMethod)),
            )
        )

    try:
        result = await client.call("searchStarsGiveawayRecipient", {"query": channel}, page_url=STARS_GIVEAWAY_PAGE)
        recipient = result.get("found", {}).get("recipient")
        if not recipient:
            raise UserNotFoundError(UserNotFoundError.NOT_FOUND.format(username=channel))

        await client.call(
            "updateStarsGiveawayState",
            {"mode": "new", "lv": "false", "dh": _state_nonce()},
            page_url=STARS_GIVEAWAY_PAGE,
        )
        await client.call(
            "updateStarsGiveawayPrices",
            {"quantity": winners, "stars": amount},
            page_url=STARS_GIVEAWAY_PAGE,
        )

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
                "device": json.dumps(DEVICE_INFO),
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

    except FragmentError as exc:
        logger.error(
            "Failed to run Stars giveaway for channel '%s' (winners=%s, amount=%s, payment_method='%s'): %s",
            channel,
            winners,
            amount,
            payment_method,
            exc,
            exc_info=True,
        )
        raise
    except Exception as exc:
        logger.exception(
            "Failed to run Stars giveaway for channel '%s' (winners=%s, amount=%s, payment_method='%s') due to an unexpected error",
            channel,
            winners,
            amount,
            payment_method,
        )
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc


async def giveaway_premium(
    client: FragmentClient,
    channel: str,
    winners: int,
    months: int = 3,
    payment_method: PaymentMethod = PaymentMethod.TON,
) -> PremiumGiveawayResult:
    if not isinstance(winners, int) or not (PREMIUM_WINNERS_MIN <= winners <= PREMIUM_WINNERS_MAX):
        raise ConfigurationError(ConfigurationError.INVALID_WINNERS_PREMIUM)
    if months not in PREMIUM_MONTHS_VALID:
        raise ConfigurationError(ConfigurationError.INVALID_MONTHS)
    if not any(payment_method == m for m in PaymentMethod):
        raise ConfigurationError(
            ConfigurationError.INVALID_PAYMENT_METHOD.format(
                method=payment_method,
                supported=", ".join(sorted(m.value for m in PaymentMethod)),
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

        await client.call(
            "updatePremiumGiveawayState",
            {
                "mode": "new",
                "lv": "false",
                "dh": _state_nonce(),
                "quantity": "",
            },
            page_url=PREMIUM_GIVEAWAY_PAGE,
        )
        await client.call(
            "updatePremiumGiveawayPrices",
            {"quantity": winners},
            page_url=PREMIUM_GIVEAWAY_PAGE,
        )

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
                "device": json.dumps(DEVICE_INFO),
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

    except FragmentError as exc:
        logger.error(
            "Failed to run Premium giveaway for channel '%s' (winners=%s, months=%s, payment_method='%s'): %s",
            channel,
            winners,
            months,
            payment_method,
            exc,
            exc_info=True,
        )
        raise
    except Exception as exc:
        logger.exception(
            "Failed to run Premium giveaway for channel '%s' (winners=%s, months=%s, payment_method='%s') due to an unexpected error",
            channel,
            winners,
            months,
            payment_method,
        )
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc
