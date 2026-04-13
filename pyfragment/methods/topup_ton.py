import json
from typing import TYPE_CHECKING

from pyfragment.types import (
    AdsTopupResult,
    ConfigurationError,
    FragmentAPIError,
    FragmentError,
    UnexpectedError,
    UserNotFoundError,
    VerificationError,
)
from pyfragment.types.constants import ADS_TOPUP_PAGE, DEVICE
from pyfragment.utils import get_account_info, process_transaction

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


async def topup_ton(client: "FragmentClient", username: str, amount: int, show_sender: bool = True) -> AdsTopupResult:
    """Topup ton to recipient's Telegram balance.

    Args:
        client: Authenticated :class:`FragmentClient` instance.
        username: Recipient's Telegram username (with or without ``@``).
        amount: Amount in TON — integer from ``1`` to ``1 000 000 000``.
        show_sender: Show your name as the sender. Defaults to ``True``.

    Returns:
        :class:`AdsTopupResult` with ``transaction_id``, ``username``, and ``amount``.

    Raises:
        ConfigurationError: If ``amount`` is not an integer between 1 and 1 000 000 000.
        UserNotFoundError: If the recipient is not found on Fragment.
        FragmentAPIError: If the Fragment API returns an error.
        UnexpectedError: For any other unexpected failure.
    """
    if not isinstance(amount, int) or not (1 <= amount <= 1_000_000_000):
        raise ConfigurationError(ConfigurationError.INVALID_TON_AMOUNT)

    try:
        await client.call("updateAdsTopupState", {"mode": "new"}, page_url=ADS_TOPUP_PAGE)

        result = await client.call("searchAdsTopupRecipient", {"query": username}, page_url=ADS_TOPUP_PAGE)
        recipient = result.get("found", {}).get("recipient")
        if not recipient:
            raise UserNotFoundError(UserNotFoundError.NOT_FOUND.format(username=username))

        result = await client.call("initAdsTopupRequest", {"recipient": recipient, "amount": amount}, page_url=ADS_TOPUP_PAGE)
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

        tx_hash = await process_transaction(client, transaction)
        return AdsTopupResult(transaction_id=tx_hash, username=username, amount=amount)

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc
