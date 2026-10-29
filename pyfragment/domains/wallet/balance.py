from __future__ import annotations

import logging
from decimal import Decimal
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

from tonutils.contracts.jetton import get_wallet_address_get_method, get_wallet_data_get_method
from tonutils.exceptions import ProviderResponseError, RunGetMethodError

from pyfragment.constants import (
    GRAM_CURRENCY,
    GRAM_DECIMALS,
    MIN_USDT_BALANCE,
    TVM_EXIT_ACCOUNT_NOT_FOUND,
    USDT_CURRENCY,
    USDT_DECIMALS,
    USDT_GRAM_MASTER_ADDRESS,
)
from pyfragment.domains.wallet.models import WalletInfo
from pyfragment.domains.wallet.wallet import provider_error
from pyfragment.enums import PaymentMethod
from pyfragment.exceptions import InsufficientBalanceError, ProviderError
from pyfragment.utils.money import from_units, to_units

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


logger = logging.getLogger(__name__)


def _is_missing_jetton_wallet(exc: Exception) -> bool:
    """Whether the owner simply has no USDT jetton wallet yet: tonapi answers 404, toncenter a TVM exit code -13."""
    if isinstance(exc, ProviderResponseError):
        return exc.code == HTTPStatus.NOT_FOUND
    return isinstance(exc, RunGetMethodError) and exc.exit_code == TVM_EXIT_ACCOUNT_NOT_FOUND


async def get_usdt_balance(ton: Any, wallet_address: str) -> int:
    """The USDT balance of a GRAM (ex TON) wallet, in units of 10^-6 USDT. Raises ``ProviderError`` if it can't be read."""
    try:
        jetton_wallet_address = await get_wallet_address_get_method(
            client=ton, address=USDT_GRAM_MASTER_ADDRESS, owner_address=wallet_address
        )
        wallet_data = await get_wallet_data_get_method(client=ton, address=jetton_wallet_address)
        return int(wallet_data[0]) if wallet_data else 0
    except Exception as exc:
        if _is_missing_jetton_wallet(exc):
            logger.debug("No USDT jetton wallet found for '%s'; treating balance as 0", wallet_address)
            return 0
        raise provider_error(ProviderError.BALANCE_CHECK_FAILED, exc, currency=USDT_CURRENCY) from exc


async def check_payment_balance(
    client: FragmentClient,
    payment_method: PaymentMethod,
    amount_nano: int,
    invoice_amount: Decimal | None,
    usdt_owner: str,
) -> Any:
    """Verify the wallet can pay before anything is signed, and return the fetched on-chain state.

    For a GRAM (ex TON) payment ``invoice_amount`` is in GRAM (ex TON); for a USDT one it is in USDT and the transfer only
    carries the GRAM (ex TON) that pays the jetton transfer's fees.
    """
    ton_wallet = client.ton_wallet
    try:
        onchain = await ton_wallet.state()
        balance_nano = int(onchain.balance)
    except Exception as exc:
        raise provider_error(ProviderError.BALANCE_CHECK_FAILED, exc, currency=GRAM_CURRENCY) from exc

    # The gas reserve comes on top of the payment: the transfer also spends GRAM (ex TON) on storage, gas and fees.
    # For a GRAM (ex TON) payment Fragment's invoice is the price if it is higher than what the transfer carries.
    price_nano = amount_nano
    if payment_method == PaymentMethod.GRAM and invoice_amount is not None and invoice_amount > 0:
        price_nano = max(price_nano, to_units(invoice_amount, GRAM_DECIMALS))
    required_nano = price_nano + client.gas_reserve_nano
    if balance_nano < required_nano:
        raise InsufficientBalanceError(
            from_units(balance_nano, GRAM_DECIMALS), from_units(required_nano, GRAM_DECIMALS), GRAM_CURRENCY
        )

    if payment_method == PaymentMethod.USDT_GRAM:
        usdt_units = await get_usdt_balance(await ton_wallet.ton(), usdt_owner)
        required_usdt = to_units(invoice_amount if invoice_amount is not None else MIN_USDT_BALANCE, USDT_DECIMALS)
        if usdt_units < required_usdt:
            raise InsufficientBalanceError(
                from_units(usdt_units, USDT_DECIMALS), from_units(required_usdt, USDT_DECIMALS), USDT_CURRENCY
            )

    return onchain


async def get_wallet_info(client: FragmentClient) -> WalletInfo:
    """Fetch the wallet address, chain state, and GRAM (ex TON)/USDT balances."""
    ton_wallet = client.ton_wallet
    wallet = ton_wallet.wallet()
    try:
        onchain = await ton_wallet.state()
    except Exception as exc:
        raise provider_error(ProviderError.WALLET_INFO_FAILED, exc) from exc

    wallet_address = wallet.address.to_str(False, False)
    usdt_balance: Decimal | None
    try:
        usdt_balance = from_units(await get_usdt_balance(await ton_wallet.ton(), wallet_address), USDT_DECIMALS)
    except ProviderError:
        # The GRAM balance is already known good; don't lose it over a failed
        # USDT lookup. Report the USDT balance as unknown (None), not as 0.
        logger.debug("USDT balance check failed for wallet '%s'; reporting it as unknown", wallet_address, exc_info=True)
        usdt_balance = None
    return WalletInfo(
        address=wallet.address.to_str(is_user_friendly=True, is_bounceable=False),
        state=onchain.state.value,
        gram_balance=from_units(int(onchain.balance), GRAM_DECIMALS),
        usdt_balance=usdt_balance,
    )
