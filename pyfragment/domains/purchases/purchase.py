from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pyfragment.core.constants import (
    PREMIUM_MONTHS_VALID,
    PREMIUM_PAGE,
    STARS_PAGE,
    STARS_PURCHASE_MAX,
    STARS_PURCHASE_MIN,
)
from pyfragment.core.validation import is_int_in_range
from pyfragment.domains.base import operation
from pyfragment.domains.payments import PurchaseFlow, new_state_params, run_purchase, validate_payment_method
from pyfragment.domains.purchases.models import PremiumResult, StarsResult
from pyfragment.domains.recipients import find_user
from pyfragment.enums import ApiMethod, PaymentMethod
from pyfragment.exceptions import ConfigurationError

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


logger = logging.getLogger(__name__)

STARS_FLOW = PurchaseFlow(
    page_url=STARS_PAGE,
    state_method=ApiMethod.UPDATE_STARS_BUY_STATE,
    init_method=ApiMethod.INIT_BUY_STARS_REQUEST,
    link_method=ApiMethod.GET_BUY_STARS_LINK,
    label="Stars purchase",
)

PREMIUM_FLOW = PurchaseFlow(
    page_url=PREMIUM_PAGE,
    state_method=ApiMethod.UPDATE_PREMIUM_STATE,
    init_method=ApiMethod.INIT_GIFT_PREMIUM_REQUEST,
    link_method=ApiMethod.GET_GIFT_PREMIUM_LINK,
    label="Premium purchase",
)


async def purchase_stars(
    client: FragmentClient,
    username: str,
    amount: int,
    show_sender: bool = True,
    payment_method: PaymentMethod = PaymentMethod.GRAM,
) -> StarsResult:
    if not is_int_in_range(amount, STARS_PURCHASE_MIN, STARS_PURCHASE_MAX):
        raise ConfigurationError(ConfigurationError.INVALID_STARS_AMOUNT)
    validate_payment_method(payment_method)

    with operation(logger, "purchase %s Stars for user '%s' using '%s'", amount, username, payment_method):
        recipient = await find_user(
            client, ApiMethod.SEARCH_STARS_RECIPIENT, STARS_FLOW.page_url, {"query": username, "quantity": ""}, username
        )
        await client.call(STARS_FLOW.state_method, new_state_params(), page_url=STARS_FLOW.page_url)
        receipt = await run_purchase(
            client,
            STARS_FLOW,
            {"recipient": recipient, "quantity": amount, "payment_method": payment_method},
            {"show_sender": int(show_sender)},
            payment_method,
        )
        return StarsResult(transaction_id=receipt.transaction_id, username=username, amount=amount, confirmed=receipt.confirmed)


async def purchase_premium(
    client: FragmentClient,
    username: str,
    months: int,
    show_sender: bool = True,
    payment_method: PaymentMethod = PaymentMethod.GRAM,
) -> PremiumResult:
    if months not in PREMIUM_MONTHS_VALID:
        raise ConfigurationError(ConfigurationError.INVALID_MONTHS)
    validate_payment_method(payment_method)

    with operation(logger, "purchase %s months of Premium for user '%s' using '%s'", months, username, payment_method):
        recipient = await find_user(
            client,
            ApiMethod.SEARCH_PREMIUM_GIFT_RECIPIENT,
            PREMIUM_FLOW.page_url,
            {"query": username, "months": months},
            username,
        )
        await client.call(PREMIUM_FLOW.state_method, new_state_params(), page_url=PREMIUM_FLOW.page_url)
        receipt = await run_purchase(
            client,
            PREMIUM_FLOW,
            {"recipient": recipient, "months": months, "payment_method": payment_method},
            {"show_sender": int(show_sender)},
            payment_method,
        )
        return PremiumResult(
            transaction_id=receipt.transaction_id, username=username, amount=months, confirmed=receipt.confirmed
        )
