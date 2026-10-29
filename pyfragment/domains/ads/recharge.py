from __future__ import annotations

import logging
from dataclasses import asdict
from typing import TYPE_CHECKING

from pyfragment.constants import ADS_TOPUP_PAGE, GRAM_TOPUP_MAX, GRAM_TOPUP_MIN
from pyfragment.domains.ads.models import AdsRechargeResult
from pyfragment.domains.base import operation
from pyfragment.domains.payments import PurchaseFlow, run_purchase
from pyfragment.enums import ApiMethod
from pyfragment.exceptions import ConfigurationError
from pyfragment.utils.validation import is_int_in_range

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


logger = logging.getLogger(__name__)

RECHARGE_FLOW = PurchaseFlow(
    page_url=ADS_TOPUP_PAGE,
    state_method=ApiMethod.UPDATE_ADS_STATE,
    init_method=ApiMethod.INIT_ADS_RECHARGE_REQUEST,
    link_method=ApiMethod.GET_ADS_RECHARGE_LINK,
    label="Ads recharge",
    versioned_state=False,
)


async def recharge_ads(client: FragmentClient, account: str, amount: int) -> AdsRechargeResult:
    if not is_int_in_range(amount, GRAM_TOPUP_MIN, GRAM_TOPUP_MAX):
        raise ConfigurationError(ConfigurationError.INVALID_GRAM_AMOUNT)

    with operation(logger, "recharge Ads account '%s' for %s GRAM (ex TON)", account, amount):
        await RECHARGE_FLOW.open(client)
        payment = await run_purchase(client, RECHARGE_FLOW, {"account": account, "amount": amount})
        return AdsRechargeResult(
            **asdict(payment),
            amount=amount,
        )
