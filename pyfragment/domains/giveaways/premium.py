from __future__ import annotations

import logging
from dataclasses import asdict
from typing import TYPE_CHECKING

from pyfragment.constants.fragment import PREMIUM_GIVEAWAY_PAGE
from pyfragment.constants.limits import PREMIUM_WINNERS
from pyfragment.domains.base import operation
from pyfragment.domains.giveaways.models import PremiumGiveawayResult
from pyfragment.domains.payments import PurchaseFlow, run_purchase
from pyfragment.domains.recipients import find_channel
from pyfragment.enums import ApiMethod, PaymentMethod
from pyfragment.utils.validation import check_limit, check_months, validate_payment_method

if TYPE_CHECKING:
    from pyfragment.client.base import BaseClient


logger = logging.getLogger(__name__)

PREMIUM_GIVEAWAY_FLOW = PurchaseFlow(
    page_url=PREMIUM_GIVEAWAY_PAGE,
    state_method=ApiMethod.UPDATE_PREMIUM_GIVEAWAY_STATE,
    init_method=ApiMethod.INIT_GIVEAWAY_PREMIUM_REQUEST,
    link_method=ApiMethod.GET_GIVEAWAY_PREMIUM_LINK,
    label="Premium giveaway",
    wallet_in_link=False,
)


async def giveaway_premium(
    client: BaseClient,
    channel: str,
    winners: int,
    months: int = 3,
    payment_method: PaymentMethod = PaymentMethod.GRAM,
) -> PremiumGiveawayResult:
    check_limit(PREMIUM_WINNERS, winners)
    check_months(months)
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
