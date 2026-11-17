from __future__ import annotations

import logging
from dataclasses import asdict
from typing import TYPE_CHECKING

from pyfragment.constants.fragment import STARS_GIVEAWAY_PAGE
from pyfragment.constants.limits import STARS_GIVEAWAY, STARS_WINNERS
from pyfragment.domains.base import operation
from pyfragment.domains.giveaways.models import StarsGiveawayResult
from pyfragment.domains.payments import PurchaseFlow, run_purchase
from pyfragment.domains.recipients import find_channel
from pyfragment.enums import ApiMethod, PaymentMethod
from pyfragment.utils.validation import check_limit, validate_payment_method

if TYPE_CHECKING:
    from pyfragment.client.base import BaseClient


logger = logging.getLogger(__name__)

STARS_GIVEAWAY_FLOW = PurchaseFlow(
    page_url=STARS_GIVEAWAY_PAGE,
    state_method=ApiMethod.UPDATE_STARS_GIVEAWAY_STATE,
    init_method=ApiMethod.INIT_GIVEAWAY_STARS_REQUEST,
    link_method=ApiMethod.GET_GIVEAWAY_STARS_LINK,
    label="Stars giveaway",
    wallet_in_link=False,
)


async def giveaway_stars(
    client: BaseClient,
    channel: str,
    winners: int,
    amount: int,
    payment_method: PaymentMethod = PaymentMethod.GRAM,
) -> StarsGiveawayResult:
    check_limit(STARS_WINNERS, winners)
    check_limit(STARS_GIVEAWAY, amount)
    validate_payment_method(payment_method)

    with operation(
        logger,
        "run Stars giveaway (channel=%s, winners=%s, amount=%s, payment_method=%s)",
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
