from __future__ import annotations

import json
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
from pyfragment.types.constants import DEVICE, STARS_PAGE
from pyfragment.utils import get_account_info, process_transaction

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


async def purchase_stars(client: "FragmentClient", username: str, amount: int, show_sender: bool = True) -> StarsResult:
    """Send Telegram Stars to a user.

    Args:
        client: Authenticated :class:`FragmentClient` instance.
        username: Recipient's Telegram username (with or without ``@``).
        amount: Number of Stars to send — integer from ``50`` to ``1 000 000``.
        show_sender: Show your name as the gift sender. Defaults to ``True``.

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

    try:
        result = await client.call("searchStarsRecipient", {"query": username, "quantity": ""}, page_url=STARS_PAGE)
        recipient = result.get("found", {}).get("recipient")
        if not recipient:
            raise UserNotFoundError(UserNotFoundError.NOT_FOUND.format(username=username))

        result = await client.call("initBuyStarsRequest", {"recipient": recipient, "quantity": amount}, page_url=STARS_PAGE)
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

        tx_hash = await process_transaction(client, transaction)
        return StarsResult(transaction_id=tx_hash, username=username, amount=amount)

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc
