from __future__ import annotations

from typing import Any

from tonutils.contracts.jetton import get_wallet_address_get_method, get_wallet_data_get_method
from tonutils.exceptions import ProviderResponseError

from pyfragment.types import WalletError
from pyfragment.types.constants import MIN_TON_BALANCE, MIN_USDT_BALANCE, USDT_TON_MASTER_ADDRESS


async def get_usdt_balance(ton: Any, wallet_address: str) -> float:
    """Return wallet USDT balance via tonutils jetton get-methods."""
    try:
        jetton_wallet_address = await get_wallet_address_get_method(
            client=ton,
            address=USDT_TON_MASTER_ADDRESS,
            owner_address=wallet_address,
        )
        wallet_data = await get_wallet_data_get_method(client=ton, address=jetton_wallet_address)
        raw_balance = int(wallet_data[0]) if wallet_data else 0
        return float(raw_balance) / 1_000_000.0
    except ProviderResponseError as exc:
        # No jetton wallet deployed yet -> effectively zero USDT balance.
        if exc.code == 404:
            return 0.0
        raise WalletError(WalletError.USDT_BALANCE_CHECK_FAILED.format(exc=exc)) from exc
    except Exception as exc:
        raise WalletError(WalletError.USDT_BALANCE_CHECK_FAILED.format(exc=exc)) from exc


async def check_ton_payment_balance(
    balance_ton: float,
    amount_ton: float,
    required_payment_amount: float | None,
) -> None:
    """Validate balance requirements for TON payment method."""
    tx_price_ton = amount_ton
    if required_payment_amount is not None and required_payment_amount > 0:
        tx_price_ton = max(tx_price_ton, required_payment_amount)

    required_ton = max(tx_price_ton, MIN_TON_BALANCE)
    if balance_ton < required_ton:
        raise WalletError(
            WalletError.LOW_TON_BALANCE.format(
                balance=balance_ton,
                required=required_ton,
            )
        )


async def check_usdt_payment_balance(
    balance_ton: float,
    required_payment_amount: float | None,
    ton: Any,
    wallet_address: str,
) -> None:
    """Validate balance requirements for USDT payment method."""
    # USDT payment still needs TON for network fees.
    if balance_ton < MIN_TON_BALANCE:
        raise WalletError(
            WalletError.LOW_TON_BALANCE.format(
                balance=balance_ton,
                required=MIN_TON_BALANCE,
            )
        )

    usdt_balance = await get_usdt_balance(ton, wallet_address)
    required_usdt = required_payment_amount if required_payment_amount is not None else MIN_USDT_BALANCE
    if usdt_balance < required_usdt:
        raise WalletError(WalletError.LOW_USDT_BALANCE.format(balance=usdt_balance, required=required_usdt))
