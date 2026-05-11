from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING

from pyfragment.types import (
    ConfigurationError,
    FragmentAPIError,
    FragmentError,
    StarsResult,
    UnexpectedError,
    UserNotFoundError,
    VerificationError,
)
from pyfragment.types.constants import DEVICE, STARS_PAGE, SUPPORTED_PAYMENT_METHODS, PaymentMethod
from pyfragment.utils import get_account_info, parse_required_payment_amount, process_transaction

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


async def purchase_stars(
    client: FragmentClient, username: str, amount: int, show_sender: bool = True, payment_method: PaymentMethod = "ton"
) -> StarsResult:
    """Send Telegram Stars to a user.

    Args:
        client: Authenticated :class:`FragmentClient` instance.
        username: Recipient identifier — ``@username``, ``username``, or ``https://t.me/username``.
        amount: Number of Stars to send — integer from ``50`` to ``1 000 000``.
        show_sender: Show your name as the gift sender. Defaults to ``True``.
        payment_method: Payment currency — ``"ton"`` (default) or ``"usdt_ton"``.

    Returns:
        :class:`StarsResult` with ``transaction_id``, ``username``, and ``amount``.

    Raises:
        ConfigurationError: If ``amount`` is not an integer between 50 and 1 000 000.
        UserNotFoundError: If the user is not found on Fragment.
        FragmentAPIError: If the Fragment API returns an error.
        UnexpectedError: For any other unexpected failure.
    """
    if not isinstance(amount, int) or not (50 <= amount <= 1_000_000):
        raise ConfigurationError(ConfigurationError.INVALID_STARS_AMOUNT)
    if payment_method not in SUPPORTED_PAYMENT_METHODS:
        raise ConfigurationError(
            ConfigurationError.INVALID_PAYMENT_METHOD.format(
                method=payment_method,
                supported=", ".join(sorted(SUPPORTED_PAYMENT_METHODS)),
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
        required_payment_amount = parse_required_payment_amount(result, payment_method)
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
