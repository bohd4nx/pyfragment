from __future__ import annotations

import json
from typing import TYPE_CHECKING

from pyfragment.core.constants import ADS_TOPUP_PAGE, DEVICE
from pyfragment.domains.wallet.info import get_account_info
from pyfragment.domains.wallet.transaction import process_transaction
from pyfragment.exceptions import ConfigurationError, FragmentAPIError, FragmentError, UnexpectedError, VerificationError
from pyfragment.models.payments import AdsRechargeResult

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


async def recharge_ads(client: FragmentClient, account: str, amount: int) -> AdsRechargeResult:
    if not isinstance(amount, int) or not (1 <= amount <= 1_000_000_000):
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
                "device": DEVICE,
                "transaction": 1,
                "id": req_id,
            },
            page_url=ADS_TOPUP_PAGE,
        )
        if transaction.get("need_verify"):
            raise VerificationError(VerificationError.KYC_REQUIRED)

        tx_hash = await process_transaction(client, transaction)
        return AdsRechargeResult(transaction_id=tx_hash, amount=amount)

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc
