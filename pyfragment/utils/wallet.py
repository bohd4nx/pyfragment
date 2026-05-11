from __future__ import annotations

import asyncio
import base64
import random
import ssl
from typing import TYPE_CHECKING, Any

from ton_core import NetworkGlobalID
from tonutils.clients import TonapiClient
from tonutils.contracts.jetton import get_wallet_address_get_method, get_wallet_data_get_method
from tonutils.exceptions import ProviderResponseError

from pyfragment.types import TransactionError, WalletError, WalletInfo
from pyfragment.types.constants import (
    MIN_TON_BALANCE,
    MIN_USDT_BALANCE,
    USDT_TON_MASTER_ADDRESS,
    WALLET_CLASSES,
    PaymentMethod,
)
from pyfragment.utils.decoder import clean_decode

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


async def _get_usdt_balance(ton: Any, wallet_address: str) -> float:
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


async def _check_ton_payment_balance(
    balance_ton: float,
    amount_ton: float,
    required_payment_amount: float | None,
    ton: Any,
    wallet_address: str,
) -> None:
    """Validate balance requirements for TON payment method."""
    del ton
    del wallet_address

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


async def _check_usdt_payment_balance(
    balance_ton: float,
    amount_ton: float,
    required_payment_amount: float | None,
    ton: Any,
    wallet_address: str,
) -> None:
    """Validate balance requirements for USDT payment method."""
    del amount_ton

    # USDT payment still needs TON for network fees.
    if balance_ton < MIN_TON_BALANCE:
        raise WalletError(
            WalletError.LOW_TON_BALANCE.format(
                balance=balance_ton,
                required=MIN_TON_BALANCE,
            )
        )

    usdt_balance = await _get_usdt_balance(ton, wallet_address)
    required_usdt = required_payment_amount if required_payment_amount is not None else MIN_USDT_BALANCE
    if usdt_balance < required_usdt:
        raise WalletError(WalletError.LOW_USDT_BALANCE.format(balance=usdt_balance, required=required_usdt))


async def process_transaction(
    client: FragmentClient,
    transaction_data: dict[str, Any],
    payment_method: PaymentMethod = "ton",
    required_payment_amount: float | None = None,
) -> str:
    """Sign and broadcast a Fragment transaction to the TON network.

    Validates the payload structure, checks the wallet balance, decodes the
    on-chain comment, and calls ``wallet.transfer``.

    Args:
        client: Authenticated :class:`FragmentClient` instance.
        transaction_data: Raw transaction dict from ``execute_transaction_request``.
        payment_method: Payment currency — ``"ton"`` or ``"usdt_ton"``.
        required_payment_amount: Optional price from init*Request response.

    Returns:
        Normalised transaction hash string.

    Raises:
        TransactionError: If the payload is malformed or the broadcast fails.
        WalletError: If the wallet balance is too low or cannot be fetched.
    """
    if "transaction" not in transaction_data or not transaction_data["transaction"].get("messages"):
        raise TransactionError(TransactionError.INVALID_PAYLOAD)

    message = transaction_data["transaction"]["messages"][0]
    amount_ton = int(message["amount"]) / 1_000_000_000

    async with TonapiClient(network=NetworkGlobalID.MAINNET, api_key=client.api_key) as ton:
        wallet_cls = WALLET_CLASSES[client.wallet_version]
        wallet, _, _, _ = wallet_cls.from_mnemonic(client=ton, mnemonic=client.seed)

        # Check balance covers selected payment flow requirements.
        try:
            await wallet.refresh()
            balance_ton = wallet.balance / 1_000_000_000
            wallet_address = wallet.address.to_str(False, False)
            checkers = {
                "ton": _check_ton_payment_balance,
                "usdt_ton": _check_usdt_payment_balance,
            }
            checker = checkers[payment_method]
            await checker(
                balance_ton,
                amount_ton,
                required_payment_amount,
                ton,
                wallet_address,
            )
        except WalletError:
            raise
        except Exception as exc:
            raise WalletError(WalletError.TON_BALANCE_CHECK_FAILED.format(exc=exc)) from exc

        try:
            raw_payload = str(message.get("payload", ""))
            payload = clean_decode(raw_payload)

            for attempt in range(3):
                try:
                    result = await wallet.transfer(
                        destination=message["address"],
                        amount=int(message["amount"]),  # nanotons, not TON
                        body=payload,
                    )
                    return str(result.normalized_hash)
                except ProviderResponseError as exc:
                    if exc.code == 429 and attempt == 0:
                        await asyncio.sleep(1 + random.uniform(0, 0.5))
                        continue
                    if exc.code == 406 and "seqno" in str(exc).lower():
                        # Previous tx seqno not yet confirmed — wallet will re-fetch seqno on retry
                        if attempt < 2:
                            await asyncio.sleep(2 + random.uniform(0, 1))
                            continue
                        raise TransactionError(TransactionError.DUPLICATE_SEQNO) from exc
                    raise
        except (WalletError, TransactionError):
            raise
        except Exception as exc:
            cause: BaseException | None = exc
            while cause is not None:
                if isinstance(cause, ssl.SSLError):
                    raise TransactionError(TransactionError.BROADCAST_FAILED_SSL.format(exc=exc)) from exc
                cause = cause.__cause__ or cause.__context__
            raise TransactionError(TransactionError.BROADCAST_FAILED.format(exc=exc)) from exc

    raise TransactionError(TransactionError.BROADCAST_FAILED.format(exc="transfer loop exited without result"))


async def get_account_info(client: FragmentClient) -> dict[str, Any]:
    """Fetch wallet address, public key, and state-init for the Fragment API.

    Fragment requires account info to build each transaction payload. The
    returned dict is JSON-serialised and passed as the ``account`` field in
    ``getBuy*Link`` / ``get*Link`` requests.

    Args:
        client: Authenticated :class:`FragmentClient` instance.

    Returns:
        Dict with ``address``, ``publicKey``, ``chain``, ``walletStateInit``.

    Raises:
        WalletError: If account info cannot be retrieved.
    """
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
            raise WalletError(WalletError.ACCOUNT_INFO_FAILED.format(exc=exc)) from exc


async def get_wallet_info(client: FragmentClient) -> WalletInfo:
    """Return the address, state and balance of the TON wallet.

    Args:
        client: Authenticated :class:`FragmentClient` instance.

    Returns:
        :class:`WalletInfo` with ``address``, ``state``, ``balance`` in TON,
        and ``usdt_balance`` in USDT.

    Raises:
        WalletError: If the wallet state cannot be fetched.
    """
    async with TonapiClient(network=NetworkGlobalID.MAINNET, api_key=client.api_key) as ton:
        try:
            wallet_cls = WALLET_CLASSES[client.wallet_version]
            wallet, _, _, _ = wallet_cls.from_mnemonic(client=ton, mnemonic=client.seed)
            await wallet.refresh()
            wallet_address = wallet.address.to_str(False, False)
            usdt_balance = await _get_usdt_balance(ton, wallet_address)
            return WalletInfo(
                address=wallet.address.to_str(is_user_friendly=True, is_bounceable=False),
                state=wallet.state.value,
                ton_balance=round(wallet.balance / 1_000_000_000, 4),
                usdt_balance=round(usdt_balance, 4),
            )
        except Exception as exc:
            raise WalletError(WalletError.WALLET_INFO_FAILED.format(exc=exc)) from exc
