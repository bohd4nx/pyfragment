from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pyfragment.core.constants import (
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
from pyfragment.core.validation import is_int_in_range
from pyfragment.domains.base import operation
from pyfragment.domains.giveaways.models import PremiumGiveawayResult, StarsGiveawayResult
from pyfragment.domains.payments import PurchaseFlow, new_state_params, run_purchase, validate_payment_method
from pyfragment.domains.recipients import find_channel
from pyfragment.enums import ApiMethod, PaymentMethod
from pyfragment.exceptions import ConfigurationError

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


logger = logging.getLogger(__name__)

STARS_GIVEAWAY_FLOW = PurchaseFlow(
    page_url=STARS_GIVEAWAY_PAGE,
    state_method=ApiMethod.UPDATE_STARS_GIVEAWAY_STATE,
    init_method=ApiMethod.INIT_GIVEAWAY_STARS_REQUEST,
    link_method=ApiMethod.GET_GIVEAWAY_STARS_LINK,
    label="Stars giveaway",
)

PREMIUM_GIVEAWAY_FLOW = PurchaseFlow(
    page_url=PREMIUM_GIVEAWAY_PAGE,
    state_method=ApiMethod.UPDATE_PREMIUM_GIVEAWAY_STATE,
    init_method=ApiMethod.INIT_GIVEAWAY_PREMIUM_REQUEST,
    link_method=ApiMethod.GET_GIVEAWAY_PREMIUM_LINK,
    label="Premium giveaway",
)


async def giveaway_stars(
    client: FragmentClient,
    channel: str,
    winners: int,
    amount: int,
    payment_method: PaymentMethod = PaymentMethod.GRAM,
) -> StarsGiveawayResult:
    if not is_int_in_range(winners, STARS_WINNERS_MIN, STARS_WINNERS_MAX):
        raise ConfigurationError(ConfigurationError.INVALID_WINNERS_STARS)
    if not is_int_in_range(amount, STARS_GIVEAWAY_MIN, STARS_GIVEAWAY_MAX):
        raise ConfigurationError(ConfigurationError.INVALID_STARS_PER_WINNER)
    validate_payment_method(payment_method)

    with operation(
        logger,
        "run Stars giveaway for channel '%s' (winners=%s, amount=%s, payment_method='%s')",
        channel,
        winners,
        amount,
        payment_method,
    ):
        recipient = await find_channel(
            client, ApiMethod.SEARCH_STARS_GIVEAWAY_RECIPIENT, STARS_GIVEAWAY_FLOW.page_url, {"query": channel}, channel
        )
        await client.call(STARS_GIVEAWAY_FLOW.state_method, new_state_params(), page_url=STARS_GIVEAWAY_FLOW.page_url)
        await client.call(
            ApiMethod.UPDATE_STARS_GIVEAWAY_PRICES,
            {"quantity": winners, "stars": amount},
            page_url=STARS_GIVEAWAY_FLOW.page_url,
        )
        receipt = await run_purchase(
            client,
            STARS_GIVEAWAY_FLOW,
            {
                "recipient": recipient,
                "quantity": str(winners),
                "stars": str(amount),
                "payment_method": payment_method,
            },
            payment_method=payment_method,
        )
        return StarsGiveawayResult(
            transaction_id=receipt.transaction_id,
            channel=channel,
            winners=winners,
            amount=amount,
            confirmed=receipt.confirmed,
        )


async def giveaway_premium(
    client: FragmentClient,
    channel: str,
    winners: int,
    months: int = 3,
    payment_method: PaymentMethod = PaymentMethod.GRAM,
) -> PremiumGiveawayResult:
    if not is_int_in_range(winners, PREMIUM_WINNERS_MIN, PREMIUM_WINNERS_MAX):
        raise ConfigurationError(ConfigurationError.INVALID_WINNERS_PREMIUM)
    if months not in PREMIUM_MONTHS_VALID:
        raise ConfigurationError(ConfigurationError.INVALID_MONTHS)
    validate_payment_method(payment_method)

    with operation(
        logger,
        "run Premium giveaway for channel '%s' (winners=%s, months=%s, payment_method='%s')",
        channel,
        winners,
        months,
        payment_method,
    ):
        recipient = await find_channel(
            client,
            ApiMethod.SEARCH_PREMIUM_GIVEAWAY_RECIPIENT,
            PREMIUM_GIVEAWAY_FLOW.page_url,
            {"query": channel, "quantity": winners, "months": months},
            channel,
        )
        await client.call(
            PREMIUM_GIVEAWAY_FLOW.state_method,
            new_state_params(quantity=""),
            page_url=PREMIUM_GIVEAWAY_FLOW.page_url,
        )
        await client.call(
            ApiMethod.UPDATE_PREMIUM_GIVEAWAY_PRICES,
            {"quantity": winners},
            page_url=PREMIUM_GIVEAWAY_FLOW.page_url,
        )
        receipt = await run_purchase(
            client,
            PREMIUM_GIVEAWAY_FLOW,
            {
                "recipient": recipient,
                "quantity": str(winners),
                "months": str(months),
                "payment_method": payment_method,
            },
            payment_method=payment_method,
        )
        return PremiumGiveawayResult(
            transaction_id=receipt.transaction_id,
            channel=channel,
            winners=winners,
            amount=months,
            confirmed=receipt.confirmed,
        )
