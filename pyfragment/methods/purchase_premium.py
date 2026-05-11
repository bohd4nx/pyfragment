from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, get_args

from pyfragment.types import (
    ConfigurationError,
    FragmentAPIError,
    FragmentError,
    PremiumResult,
    UnexpectedError,
    UserNotFoundError,
    VerificationError,
)
from pyfragment.types.constants import DEVICE, PREMIUM_PAGE, PaymentMethod
from pyfragment.utils import get_account_info, parse_required_payment_amount, process_transaction

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


async def purchase_premium(
    client: FragmentClient,
    username: str,
    months: int,
    show_sender: bool = True,
    payment_method: PaymentMethod = "ton",
) -> PremiumResult:
    """Gift Telegram Premium to a user.

    Args:
        client: Authenticated :class:`FragmentClient` instance.
        username: Recipient identifier — ``@username``, ``username``, or ``https://t.me/username``.
        months: Premium duration — ``3``, ``6``, or ``12``.
        show_sender: Show your name as the gift sender. Defaults to ``True``.
        payment_method: Payment currency — ``"ton"`` (default) or ``"usdt_ton"``.

    Returns:
        :class:`PremiumResult` with ``transaction_id``, ``username``, and ``amount``.

    Raises:
        ConfigurationError: If ``months`` is not ``3``, ``6``, or ``12``.
        UserNotFoundError: If the user is not found on Fragment.
        FragmentAPIError: If the Fragment API returns an error.
        UnexpectedError: For any other unexpected failure.
    """
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
