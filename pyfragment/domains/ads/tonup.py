from __future__ import annotations

import json
from typing import TYPE_CHECKING

from pyfragment.core.constants import ADS_TOPUP_PAGE, DEVICE
from pyfragment.domains.payments import parse_required_payment_amount
from pyfragment.domains.tonapi.account import get_account_info
from pyfragment.domains.tonapi.transaction import process_transaction
from pyfragment.exceptions import (
    ConfigurationError,
    FragmentAPIError,
    FragmentError,
    UnexpectedError,
    UserNotFoundError,
    VerificationError,
)
from pyfragment.models.payments import AdsTopupResult

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


async def topup_ton(client: FragmentClient, username: str, amount: int, show_sender: bool = True) -> AdsTopupResult:
    if not isinstance(amount, int) or not (1 <= amount <= 1_000_000_000):
        raise ConfigurationError(ConfigurationError.INVALID_TON_AMOUNT)

    try:
        await client.call("updateAdsTopupState", {"mode": "new"}, page_url=ADS_TOPUP_PAGE)

        result = await client.call("searchAdsTopupRecipient", {"query": username}, page_url=ADS_TOPUP_PAGE)
        recipient = result.get("found", {}).get("recipient")
        if not recipient:
            raise UserNotFoundError(UserNotFoundError.NOT_FOUND.format(username=username))

        result = await client.call("initAdsTopupRequest", {"recipient": recipient, "amount": amount}, page_url=ADS_TOPUP_PAGE)
        required_payment_amount = parse_required_payment_amount(result)
        req_id = result.get("req_id")
        if not req_id:
            raise FragmentAPIError(FragmentAPIError.NO_REQUEST_ID.format(context="TON topup"))

        account = await get_account_info(client)
        transaction = await client.call(
            "getAdsTopupLink",
            {
                "account": json.dumps(account),
                "device": DEVICE,
                "transaction": 1,
                "id": req_id,
                "show_sender": int(show_sender),
            },
            page_url=ADS_TOPUP_PAGE,
        )
        if transaction.get("need_verify"):
            raise VerificationError(VerificationError.KYC_REQUIRED)

        tx_hash = await process_transaction(client, transaction, required_payment_amount=required_payment_amount)
        return AdsTopupResult(transaction_id=tx_hash, username=username, amount=amount)

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc
