from __future__ import annotations

import base64
import logging
from typing import TYPE_CHECKING, Any

from ton_core import NetworkGlobalID
from tonutils.clients import TonapiClient
from tonutils.contracts.jetton import get_wallet_address_get_method, get_wallet_data_get_method
from tonutils.exceptions import ProviderResponseError

from pyfragment.core.constants import MIN_GRAM_BALANCE, MIN_USDT_BALANCE, USDT_GRAM_MASTER_ADDRESS
from pyfragment.domains.tonapi.models import WalletInfo
from pyfragment.enums import WALLET_CLASSES
from pyfragment.exceptions import WalletError

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


logger = logging.getLogger(__name__)


async def get_usdt_balance(ton: Any, wallet_address: str) -> float:
    """Return the USDT balance for a Fragment-linked GRAM (ex TON) wallet."""
    try:
        jetton_wallet_address = await get_wallet_address_get_method(
            client=ton,
            address=USDT_GRAM_MASTER_ADDRESS,
            owner_address=wallet_address,
        )
        wallet_data = await get_wallet_data_get_method(client=ton, address=jetton_wallet_address)
        raw_balance = int(wallet_data[0]) if wallet_data else 0
        return float(raw_balance) / 1_000_000.0
    except ProviderResponseError as exc:
        if exc.code == 404:
            logger.debug("No USDT jetton wallet found for '%s'; treating balance as 0", wallet_address)
            return 0.0
        logger.error("Failed to load USDT balance for wallet '%s': %s", wallet_address, exc, exc_info=True)
        raise WalletError(WalletError.USDT_BALANCE_CHECK_FAILED.format(exc=exc)) from exc
    except Exception as exc:
        logger.exception("Failed to load USDT balance for wallet '%s' due to an unexpected error", wallet_address)
        raise WalletError(WalletError.USDT_BALANCE_CHECK_FAILED.format(exc=exc)) from exc


async def check_gram_payment_balance(
    balance_gram: float,
    amount_gram: float,
    required_payment_amount: float | None,
) -> None:
    """Validate that the GRAM (ex TON) wallet can cover a GRAM (ex TON)-denominated payment."""
    tx_price_gram = amount_gram
    if required_payment_amount is not None and required_payment_amount > 0:
        tx_price_gram = max(tx_price_gram, required_payment_amount)

    required_gram = max(tx_price_gram, MIN_GRAM_BALANCE)
    if balance_gram < required_gram:
        logger.error(
            "Failed GRAM (ex TON) balance check: balance=%s GRAM (ex TON), required=%s GRAM (ex TON)",
            round(balance_gram, 6),
            round(required_gram, 6),
        )
        raise WalletError(WalletError.LOW_GRAM_BALANCE.format(balance=balance_gram, required=required_gram))


async def check_usdt_payment_balance(
    balance_gram: float,
    required_payment_amount: float | None,
    ton: Any,
    wallet_address: str,
) -> None:
    """Validate that the wallet can cover a USDT-denominated payment."""
    if balance_gram < MIN_GRAM_BALANCE:
        logger.error(
            "Failed GRAM (ex TON) gas reserve check for USDT payment: balance=%s GRAM (ex TON), required=%s GRAM (ex TON)",
            round(balance_gram, 6),
            MIN_GRAM_BALANCE,
        )
        raise WalletError(WalletError.LOW_GRAM_BALANCE.format(balance=balance_gram, required=MIN_GRAM_BALANCE))

    usdt_balance = await get_usdt_balance(ton, wallet_address)
    required_usdt = required_payment_amount if required_payment_amount is not None else MIN_USDT_BALANCE
    if usdt_balance < required_usdt:
        logger.error(
            "Failed USDT balance check for wallet '%s': balance=%s USDT, required=%s USDT",
            wallet_address,
            round(usdt_balance, 6),
            round(required_usdt, 6),
        )
        raise WalletError(WalletError.LOW_USDT_BALANCE.format(balance=usdt_balance, required=required_usdt))


async def get_account_info(client: FragmentClient) -> dict[str, Any]:
    """Build the wallet payload Fragment needs to prepare a transaction."""
    async with TonapiClient(network=NetworkGlobalID.MAINNET, api_key=client.api_key) as ton:
        try:
            wallet_cls = WALLET_CLASSES[client.wallet_version]
            wallet, pub_key, _, _ = wallet_cls.from_mnemonic(client=ton, mnemonic=client.seed)
            boc = wallet.state_init.serialize().to_boc()
            return {
                "address": wallet.address.to_str(False, False),
                "publicKey": pub_key.as_hex,
                "chain": "-239",
                "walletStateInit": base64.b64encode(boc).decode(),
            }
        except Exception as exc:
            logger.exception("Failed to build Fragment account info from the configured wallet")
            raise WalletError(WalletError.ACCOUNT_INFO_FAILED.format(exc=exc)) from exc


async def get_wallet_info(client: FragmentClient) -> WalletInfo:
    """Fetch the wallet address, chain state, and GRAM (ex TON)/USDT balances."""
    async with TonapiClient(network=NetworkGlobalID.MAINNET, api_key=client.api_key) as ton:
        try:
            wallet_cls = WALLET_CLASSES[client.wallet_version]
            wallet, _, _, _ = wallet_cls.from_mnemonic(client=ton, mnemonic=client.seed)
            await wallet.refresh()
            wallet_address = wallet.address.to_str(False, False)
            usdt_balance = await get_usdt_balance(ton, wallet_address)
            return WalletInfo(
                address=wallet.address.to_str(is_user_friendly=True, is_bounceable=False),
                state=wallet.state.value,
                gram_balance=round(wallet.balance / 1_000_000_000, 4),
                usdt_balance=round(usdt_balance, 4),
            )
        except Exception as exc:
            logger.exception("Failed to fetch wallet info from Tonapi")
            raise WalletError(WalletError.WALLET_INFO_FAILED.format(exc=exc)) from exc
