from __future__ import annotations

import logging
from dataclasses import asdict
from typing import TYPE_CHECKING

from pyfragment.constants import (
    STARS_GIVEAWAY_MAX,
    STARS_GIVEAWAY_MIN,
    STARS_GIVEAWAY_PAGE,
    STARS_WINNERS_MAX,
    STARS_WINNERS_MIN,
)
from pyfragment.domains.base import operation
from pyfragment.domains.giveaways.models import StarsGiveawayResult
from pyfragment.domains.payments import PurchaseFlow, run_purchase, validate_payment_method
from pyfragment.domains.recipients import find_channel
from pyfragment.enums import ApiMethod, PaymentMethod
from pyfragment.exceptions import ConfigurationError
from pyfragment.utils.validation import is_int_in_range

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
        await STARS_GIVEAWAY_FLOW.open(client)
        await client.call(
            ApiMethod.UPDATE_STARS_GIVEAWAY_PRICES,
            {"quantity": winners, "stars": amount},
            page_url=STARS_GIVEAWAY_FLOW.page_url,
        )
        payment = await run_purchase(
            client,
            STARS_GIVEAWAY_FLOW,
            {
                "recipient": recipient.recipient,
                "quantity": str(winners),
                "stars": str(amount),
                "payment_method": payment_method,
            },
            payment_method=payment_method,
        )
        return StarsGiveawayResult(**asdict(payment), channel=recipient.username, winners=winners, amount=amount)
