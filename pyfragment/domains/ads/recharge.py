from __future__ import annotations

import logging
from dataclasses import asdict
from typing import TYPE_CHECKING

from pyfragment.constants import ADS_TOPUP_PAGE
from pyfragment.domains.ads.models import AdsRechargeResult
from pyfragment.domains.base import operation
from pyfragment.domains.payments import PurchaseFlow, run_purchase
from pyfragment.enums import ApiMethod, Limit
from pyfragment.utils.validation import check_limit

if TYPE_CHECKING:
    from pyfragment.client.base import BaseClient


logger = logging.getLogger(__name__)

RECHARGE_FLOW = PurchaseFlow(
    page_url=ADS_TOPUP_PAGE,
    state_method=ApiMethod.UPDATE_ADS_STATE,
    init_method=ApiMethod.INIT_ADS_RECHARGE_REQUEST,
    link_method=ApiMethod.GET_ADS_RECHARGE_LINK,
    label="Ads recharge",
    versioned_state=False,
)


async def recharge_ads(client: BaseClient, account: str, amount: int) -> AdsRechargeResult:
    check_limit(Limit.GRAM_TOPUP, amount)

    with operation(logger, "recharge Ads account '%s' for %s GRAM (ex TON)", account, amount):
        await RECHARGE_FLOW.open(client)
        payment = await run_purchase(client, RECHARGE_FLOW, {"account": account, "amount": amount})
        return AdsRechargeResult(
            **asdict(payment),
            amount=amount,
        )
