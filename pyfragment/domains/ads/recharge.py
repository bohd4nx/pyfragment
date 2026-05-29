from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from pyfragment.core.constants import ADS_TOPUP_PAGE, DEVICE_INFO, TON_TOPUP_MAX, TON_TOPUP_MIN
from pyfragment.domains.tonapi.account import get_account_info
from pyfragment.domains.tonapi.transaction import process_transaction
from pyfragment.exceptions import ConfigurationError, FragmentAPIError, FragmentError, UnexpectedError, VerificationError
from pyfragment.models.payments import AdsRechargeResult

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


logger = logging.getLogger(__name__)


async def recharge_ads(client: FragmentClient, account: str, amount: int) -> AdsRechargeResult:
    if not isinstance(amount, int) or not (TON_TOPUP_MIN <= amount <= TON_TOPUP_MAX):
        raise ConfigurationError(ConfigurationError.INVALID_TON_AMOUNT)

    try:
        await client.call("updateAdsState", {"mode": "new"}, page_url=ADS_TOPUP_PAGE)

        result = await client.call("initAdsRechargeRequest", {"account": account, "amount": amount}, page_url=ADS_TOPUP_PAGE)
        req_id = result.get("req_id")
        if not req_id:
            raise FragmentAPIError(FragmentAPIError.NO_REQUEST_ID.format(context="Ads recharge"))

        account_info = await get_account_info(client)
        transaction = await client.call(
            "getAdsRechargeLink",
            {
                "account": json.dumps(account_info),
                "device": json.dumps(DEVICE_INFO),
                "transaction": 1,
                "id": req_id,
            },
            page_url=ADS_TOPUP_PAGE,
        )
        if transaction.get("need_verify"):
            raise VerificationError(VerificationError.KYC_REQUIRED)

        tx_hash = await process_transaction(client, transaction)
        return AdsRechargeResult(transaction_id=tx_hash, amount=amount)

    except FragmentError as exc:
        logger.error("Failed to recharge Ads account '%s' for %s TON: %s", account, amount, exc, exc_info=True)
        raise
    except Exception as exc:
        logger.exception("Failed to recharge Ads account '%s' for %s TON due to an unexpected error", account, amount)
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc
