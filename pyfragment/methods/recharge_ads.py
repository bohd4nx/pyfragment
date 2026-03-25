import json
from typing import TYPE_CHECKING

import httpx

from pyfragment.types import (
    ConfigurationError,
    FragmentAPIError,
    FragmentError,
    UnexpectedError,
)
from pyfragment.types.constants import ADS_TOPUP_PAGE, DEVICE
from pyfragment.types.results import AdsRechargeResult
from pyfragment.utils import (
    execute_transaction_request,
    fragment_request,
    get_account_info,
    get_fragment_hash,
    make_headers,
    process_transaction,
)

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient

HEADERS: dict[str, str] = make_headers(ADS_TOPUP_PAGE)


async def _init_request(
    session: httpx.AsyncClient,
    fragment_hash: str,
    account: str,
    amount: int,
) -> str:
    result = await fragment_request(
        session,
        fragment_hash,
        HEADERS,
        {
            "account": account,
            "amount": amount,
            "method": "initAdsRechargeRequest",
        },
    )
    req_id = result.get("req_id")
    if not req_id:
        raise FragmentAPIError(FragmentAPIError.NO_REQUEST_ID.format(context="Ads recharge"))
    return req_id


async def recharge_ads(client: "FragmentClient", account: str, amount: int) -> AdsRechargeResult:
    """Add funds to your own Telegram Ads account.

    Args:
        client: Authenticated :class:`FragmentClient` instance.
        account: Your Fragment Ads account identifier — the channel or bot username
            the Ads account is linked to (e.g. ``"@mychannel"``).
        amount: Amount in TON — integer from ``1`` to ``1 000 000 000``.

    Returns:
        :class:`AdsRechargeResult` with ``transaction_id`` and ``amount``.

    Raises:
        ConfigurationError: If ``amount`` is not a valid integer in the allowed range.
        FragmentAPIError: If the Fragment API returns an error.
        UnexpectedError: For any other unexpected failure.
    """
    if not isinstance(amount, int) or not (1 <= amount <= 1_000_000_000):
        raise ConfigurationError(ConfigurationError.INVALID_TON_AMOUNT)

    try:
        fragment_hash = await get_fragment_hash(client.cookies, HEADERS, ADS_TOPUP_PAGE, client.timeout)
        account_info = await get_account_info(client)

        async with httpx.AsyncClient(cookies=client.cookies, timeout=client.timeout) as session:
            await fragment_request(session, fragment_hash, HEADERS, {"method": "updateAdsState", "mode": "new"})
            req_id = await _init_request(session, fragment_hash, account, amount)

            tx_data = {
                "account": json.dumps(account_info),
                "device": DEVICE,
                "transaction": 1,
                "id": req_id,
                "method": "getAdsRechargeLink",
            }
            transaction = await execute_transaction_request(session, HEADERS, tx_data, fragment_hash)

        tx_hash = await process_transaction(client, transaction)
        return AdsRechargeResult(transaction_id=tx_hash, amount=amount)

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc
