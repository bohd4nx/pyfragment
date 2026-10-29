from __future__ import annotations

import logging
from dataclasses import asdict
from typing import TYPE_CHECKING

from pyfragment.constants import (
    PREMIUM_GIVEAWAY_PAGE,
    PREMIUM_MONTHS_VALID,
    PREMIUM_WINNERS_MAX,
    PREMIUM_WINNERS_MIN,
)
from pyfragment.domains.base import operation
from pyfragment.domains.giveaways.models import PremiumGiveawayResult
from pyfragment.domains.payments import PurchaseFlow, run_purchase, validate_payment_method
from pyfragment.domains.recipients import find_channel
from pyfragment.enums import ApiMethod, PaymentMethod
from pyfragment.exceptions import ConfigurationError
from pyfragment.utils.validation import is_int_in_range

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


logger = logging.getLogger(__name__)

PREMIUM_GIVEAWAY_FLOW = PurchaseFlow(
    page_url=PREMIUM_GIVEAWAY_PAGE,
    state_method=ApiMethod.UPDATE_PREMIUM_GIVEAWAY_STATE,
    init_method=ApiMethod.INIT_GIVEAWAY_PREMIUM_REQUEST,
    link_method=ApiMethod.GET_GIVEAWAY_PREMIUM_LINK,
    label="Premium giveaway",
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
        await PREMIUM_GIVEAWAY_FLOW.open(client, quantity="")
        await client.call(
            ApiMethod.UPDATE_PREMIUM_GIVEAWAY_PRICES,
            {"quantity": winners},
            page_url=PREMIUM_GIVEAWAY_FLOW.page_url,
        )
        payment = await run_purchase(
            client,
            PREMIUM_GIVEAWAY_FLOW,
            {
                "recipient": recipient.recipient,
                "quantity": str(winners),
                "months": str(months),
                "payment_method": payment_method,
            },
            payment_method=payment_method,
        )
        return PremiumGiveawayResult(**asdict(payment), channel=recipient.username, winners=winners, amount=months)
