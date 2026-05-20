from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, get_args

from pyfragment.core.constants import DEVICE, PREMIUM_PAGE, STARS_PAGE
from pyfragment.domains.payments import parse_required_payment_amount
from pyfragment.domains.wallet.info import get_account_info
from pyfragment.domains.wallet.transaction import process_transaction
from pyfragment.exceptions import (
    ConfigurationError,
    FragmentAPIError,
    FragmentError,
    UnexpectedError,
    UserNotFoundError,
    VerificationError,
)
from pyfragment.models.enums import PaymentMethod
from pyfragment.models.payments import PremiumResult, StarsResult

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


async def purchase_stars(
    client: FragmentClient,
    username: str,
    amount: int,
    show_sender: bool = True,
    payment_method: PaymentMethod = "ton",
) -> StarsResult:
    if not isinstance(amount, int) or not (50 <= amount <= 1_000_000):
        raise ConfigurationError(ConfigurationError.INVALID_STARS_AMOUNT)
    if payment_method not in get_args(PaymentMethod):
        raise ConfigurationError(
            ConfigurationError.INVALID_PAYMENT_METHOD.format(
                method=payment_method,
                supported=", ".join(sorted(get_args(PaymentMethod))),
            )
        )

    try:
        result = await client.call("searchStarsRecipient", {"query": username, "quantity": ""}, page_url=STARS_PAGE)
        recipient = result.get("found", {}).get("recipient")
        if not recipient:
            raise UserNotFoundError(UserNotFoundError.NOT_FOUND.format(username=username))

        await client.call(
            "updateStarsBuyState",
            {"mode": "new", "lv": "false", "dh": str(int(time.time()))},
            page_url=STARS_PAGE,
        )
        result = await client.call(
            "initBuyStarsRequest",
            {"recipient": recipient, "quantity": amount, "payment_method": payment_method},
            page_url=STARS_PAGE,
        )
        required_payment_amount = parse_required_payment_amount(result)
        req_id = result.get("req_id")
        if not req_id:
            raise FragmentAPIError(FragmentAPIError.NO_REQUEST_ID.format(context="Stars purchase"))

        account = await get_account_info(client)
        transaction = await client.call(
            "getBuyStarsLink",
            {
                "account": json.dumps(account),
                "device": DEVICE,
                "transaction": 1,
                "id": req_id,
                "show_sender": int(show_sender),
            },
            page_url=STARS_PAGE,
        )
        if transaction.get("need_verify"):
            raise VerificationError(VerificationError.KYC_REQUIRED)

        tx_hash = await process_transaction(
            client,
            transaction,
            payment_method=payment_method,
            required_payment_amount=required_payment_amount,
        )
        return StarsResult(transaction_id=tx_hash, username=username, amount=amount)

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc


async def purchase_premium(
    client: FragmentClient,
    username: str,
    months: int,
    show_sender: bool = True,
    payment_method: PaymentMethod = "ton",
) -> PremiumResult:
    if months not in (3, 6, 12):
        raise ConfigurationError(ConfigurationError.INVALID_MONTHS)
    if payment_method not in get_args(PaymentMethod):
        raise ConfigurationError(
            ConfigurationError.INVALID_PAYMENT_METHOD.format(
                method=payment_method,
                supported=", ".join(sorted(get_args(PaymentMethod))),
            )
        )

    try:
        result = await client.call("searchPremiumGiftRecipient", {"query": username, "months": months}, page_url=PREMIUM_PAGE)
        recipient = result.get("found", {}).get("recipient")
        if not recipient:
            raise UserNotFoundError(UserNotFoundError.NOT_FOUND.format(username=username))

        await client.call(
            "updatePremiumState",
            {"mode": "new", "lv": "false", "dh": str(int(time.time()))},
            page_url=PREMIUM_PAGE,
        )
        result = await client.call(
            "initGiftPremiumRequest",
            {"recipient": recipient, "months": months, "payment_method": payment_method},
            page_url=PREMIUM_PAGE,
        )
        required_payment_amount = parse_required_payment_amount(result)
        req_id = result.get("req_id")
        if not req_id:
            raise FragmentAPIError(FragmentAPIError.NO_REQUEST_ID.format(context="Premium purchase"))

        account = await get_account_info(client)
        transaction = await client.call(
            "getGiftPremiumLink",
            {
                "account": json.dumps(account),
                "device": DEVICE,
                "transaction": 1,
                "id": req_id,
                "show_sender": int(show_sender),
            },
            page_url=PREMIUM_PAGE,
        )
        if transaction.get("need_verify"):
            raise VerificationError(VerificationError.KYC_REQUIRED)

        tx_hash = await process_transaction(
            client,
            transaction,
            payment_method=payment_method,
            required_payment_amount=required_payment_amount,
        )
        return PremiumResult(transaction_id=tx_hash, username=username, amount=months)

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc
