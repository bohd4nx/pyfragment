from __future__ import annotations

import logging
from dataclasses import asdict
from typing import TYPE_CHECKING

from pyfragment.constants.fragment import ADS_TOPUP_PAGE
from pyfragment.constants.limits import GRAM_TOPUP
from pyfragment.domains.ads.models import AdsTopupResult
from pyfragment.domains.base import operation
from pyfragment.domains.payments import PurchaseFlow, run_purchase
from pyfragment.domains.recipients import find_user
from pyfragment.enums import ApiMethod
from pyfragment.utils.validation import check_limit

if TYPE_CHECKING:
    from pyfragment.client.base import BaseClient


logger = logging.getLogger(__name__)

TOPUP_FLOW = PurchaseFlow(
    page_url=ADS_TOPUP_PAGE,
    state_method=ApiMethod.UPDATE_ADS_TOPUP_STATE,
    init_method=ApiMethod.INIT_ADS_TOPUP_REQUEST,
    link_method=ApiMethod.GET_ADS_TOPUP_LINK,
    label="GRAM (ex TON) topup",
    versioned_state=False,
)


async def topup_gram(client: BaseClient, username: str, amount: int, show_sender: bool = True) -> AdsTopupResult:
    check_limit(GRAM_TOPUP, amount)

    with operation(logger, "top up GRAM (username=%s, amount=%s)", username, amount):
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
