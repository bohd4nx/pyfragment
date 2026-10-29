from __future__ import annotations

import logging
from dataclasses import asdict
from typing import TYPE_CHECKING

from pyfragment.constants import ADS_TOPUP_PAGE, GRAM_TOPUP_MAX, GRAM_TOPUP_MIN
from pyfragment.domains.ads.models import AdsTopupResult
from pyfragment.domains.base import operation
from pyfragment.domains.payments import PurchaseFlow, run_purchase
from pyfragment.domains.recipients import find_user
from pyfragment.enums import ApiMethod
from pyfragment.exceptions import ConfigurationError
from pyfragment.utils.validation import is_int_in_range

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


logger = logging.getLogger(__name__)

TOPUP_FLOW = PurchaseFlow(
    page_url=ADS_TOPUP_PAGE,
    state_method=ApiMethod.UPDATE_ADS_TOPUP_STATE,
    init_method=ApiMethod.INIT_ADS_TOPUP_REQUEST,
    link_method=ApiMethod.GET_ADS_TOPUP_LINK,
    label="GRAM (ex TON) topup",
    versioned_state=False,
)


async def topup_gram(client: FragmentClient, username: str, amount: int, show_sender: bool = True) -> AdsTopupResult:
    if not is_int_in_range(amount, GRAM_TOPUP_MIN, GRAM_TOPUP_MAX):
        raise ConfigurationError(ConfigurationError.INVALID_GRAM_AMOUNT)

    with operation(logger, "top up GRAM (ex TON) for user '%s' with %s GRAM (ex TON)", username, amount):
        await TOPUP_FLOW.open(client)
        recipient = await find_user(
            client, ApiMethod.SEARCH_ADS_TOPUP_RECIPIENT, TOPUP_FLOW.page_url, {"query": username}, username
        )
        payment = await run_purchase(
            client,
            TOPUP_FLOW,
            {"recipient": recipient.recipient, "amount": amount},
            {"show_sender": int(show_sender)},
        )
        return AdsTopupResult(
            **asdict(payment),
            username=recipient.username,
            amount=amount,
        )
