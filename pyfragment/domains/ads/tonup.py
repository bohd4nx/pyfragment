from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pyfragment.core.constants import ADS_TOPUP_PAGE, GRAM_TOPUP_MAX, GRAM_TOPUP_MIN
from pyfragment.core.validation import is_int_in_range
from pyfragment.domains.ads.models import AdsTopupResult
from pyfragment.domains.base import operation
from pyfragment.domains.payments import PurchaseFlow, run_purchase
from pyfragment.domains.recipients import find_user
from pyfragment.enums import ApiMethod, StateMode
from pyfragment.exceptions import ConfigurationError

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


logger = logging.getLogger(__name__)

TOPUP_FLOW = PurchaseFlow(
    page_url=ADS_TOPUP_PAGE,
    state_method=ApiMethod.UPDATE_ADS_TOPUP_STATE,
    init_method=ApiMethod.INIT_ADS_TOPUP_REQUEST,
    link_method=ApiMethod.GET_ADS_TOPUP_LINK,
    label="GRAM (ex TON) topup",
)


async def topup_gram(client: FragmentClient, username: str, amount: int, show_sender: bool = True) -> AdsTopupResult:
    if not is_int_in_range(amount, GRAM_TOPUP_MIN, GRAM_TOPUP_MAX):
        raise ConfigurationError(ConfigurationError.INVALID_GRAM_AMOUNT)

    with operation(logger, "top up GRAM (ex TON) for user '%s' with %s GRAM (ex TON)", username, amount):
        await client.call(TOPUP_FLOW.state_method, {"mode": StateMode.NEW}, page_url=TOPUP_FLOW.page_url)
        recipient = await find_user(
            client, ApiMethod.SEARCH_ADS_TOPUP_RECIPIENT, TOPUP_FLOW.page_url, {"query": username}, username
        )
        receipt = await run_purchase(
            client,
            TOPUP_FLOW,
            {"recipient": recipient, "amount": amount},
            {"show_sender": int(show_sender)},
        )
        return AdsTopupResult(
            transaction_id=receipt.transaction_id, username=username, amount=amount, confirmed=receipt.confirmed
        )
