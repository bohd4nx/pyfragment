from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pyfragment.core.constants import ADS_TOPUP_PAGE, GRAM_TOPUP_MAX, GRAM_TOPUP_MIN
from pyfragment.core.validation import is_int_in_range
from pyfragment.domains.ads.models import AdsRechargeResult
from pyfragment.domains.base import operation
from pyfragment.domains.payments import PurchaseFlow, run_purchase
from pyfragment.enums import ApiMethod, StateMode
from pyfragment.exceptions import ConfigurationError

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


logger = logging.getLogger(__name__)

RECHARGE_FLOW = PurchaseFlow(
    page_url=ADS_TOPUP_PAGE,
    state_method=ApiMethod.UPDATE_ADS_STATE,
    init_method=ApiMethod.INIT_ADS_RECHARGE_REQUEST,
    link_method=ApiMethod.GET_ADS_RECHARGE_LINK,
    label="Ads recharge",
)


async def recharge_ads(client: FragmentClient, account: str, amount: int) -> AdsRechargeResult:
    if not is_int_in_range(amount, GRAM_TOPUP_MIN, GRAM_TOPUP_MAX):
        raise ConfigurationError(ConfigurationError.INVALID_GRAM_AMOUNT)

    with operation(logger, "recharge Ads account '%s' for %s GRAM (ex TON)", account, amount):
        await client.call(RECHARGE_FLOW.state_method, {"mode": StateMode.NEW}, page_url=RECHARGE_FLOW.page_url)
        receipt = await run_purchase(client, RECHARGE_FLOW, {"account": account, "amount": amount})
        return AdsRechargeResult(transaction_id=receipt.transaction_id, amount=amount, confirmed=receipt.confirmed)
