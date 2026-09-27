from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from pyfragment.core.constants import ADS_TOPUP_PAGE, DEVICE_INFO, GRAM_TOPUP_MAX, GRAM_TOPUP_MIN
from pyfragment.core.validation import is_int_in_range
from pyfragment.domains.ads.models import AdsRechargeResult
from pyfragment.domains.payments import cancel_invoice, confirm_purchase, is_confirmed
from pyfragment.exceptions import (
    ConfigurationError,
    FragmentAPIError,
    FragmentError,
    TransactionError,
    UnexpectedError,
    VerificationError,
)
from pyfragment.services.tonapi.account import get_account_info
from pyfragment.services.tonapi.transaction import process_transaction

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


logger = logging.getLogger(__name__)


async def recharge_ads(client: FragmentClient, account: str, amount: int) -> AdsRechargeResult:
    if not is_int_in_range(amount, GRAM_TOPUP_MIN, GRAM_TOPUP_MAX):
        raise ConfigurationError(ConfigurationError.INVALID_GRAM_AMOUNT)

    try:
        await client.call("updateAdsState", {"mode": "new"}, page_url=ADS_TOPUP_PAGE)

        result = await client.call("initAdsRechargeRequest", {"account": account, "amount": amount}, page_url=ADS_TOPUP_PAGE)
        req_id = result.get("req_id")
        if not req_id:
            if result.get("error"):
                raise FragmentAPIError(str(result["error"]))
            raise FragmentAPIError(FragmentAPIError.NO_REQUEST_ID.format(context="Ads recharge"))

        try:
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

            tx_hash, tx_boc = await process_transaction(client, transaction)
        except TransactionError:
            # The broadcast itself may or may not have reached the chain; leave the invoice alone.
            raise
        except Exception:
            await cancel_invoice(client, req_id, ADS_TOPUP_PAGE)
            raise
        state_response = await confirm_purchase(client, account_info, tx_boc, transaction, "updateAdsState", ADS_TOPUP_PAGE)
        return AdsRechargeResult(transaction_id=tx_hash, amount=amount, confirmed=is_confirmed(state_response))

    except FragmentError as exc:
        logger.error("Failed to recharge Ads account '%s' for %s GRAM (ex TON): %s", account, amount, exc, exc_info=True)
        raise
    except Exception as exc:
        logger.exception("Failed to recharge Ads account '%s' for %s GRAM (ex TON) due to an unexpected error", account, amount)
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc
