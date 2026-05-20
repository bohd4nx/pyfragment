from __future__ import annotations

from typing import TYPE_CHECKING

from ton_core import Address, NetworkGlobalID
from tonutils.clients import ToncenterClient
from tonutils.contracts import JettonTransferBuilder, TONTransferBuilder

from pyfragment.core.constants import USDT_TON_MASTER_ADDRESS, WALLET_CLASSES
from pyfragment.exceptions import TransactionError, WalletError
from pyfragment.models.wallet import TonTransferResult, UsdtTransferResult

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


async def send_ton_transfer(
    client: FragmentClient,
    destination: str,
    amount: int,
    body: str | None = None,
) -> TonTransferResult:
    """Send a direct TON transfer on-chain using ToncenterClient.

    Args:
        client: Authenticated :class:`FragmentClient` instance (seed and wallet_version used).
        destination: Recipient TON address (any format, e.g. ``"UQ..."``).
        amount: Amount in nanotons (1 TON = 1 000 000 000 nanotons).
        body: Optional on-chain comment attached to the transfer.

    Returns:
        :class:`TonTransferResult` with ``transaction_id``, ``destination``, and ``amount``.

    Raises:
        TransactionError: If the transaction fails to broadcast.
    """
    try:
        async with ToncenterClient(network=NetworkGlobalID.MAINNET) as ton:
            wallet_cls = WALLET_CLASSES[client.wallet_version]
            wallet, _, _, _ = wallet_cls.from_mnemonic(client=ton, mnemonic=client.seed)
            result = await wallet.transfer_message(
                TONTransferBuilder(
                    destination=Address(destination),
                    amount=amount,
                    body=body,
                )
            )
            return TonTransferResult(
                transaction_id=str(result.normalized_hash),
                destination=destination,
                amount=amount,
            )
    except (TransactionError, WalletError):
        raise
    except Exception as exc:
        raise TransactionError(TransactionError.BROADCAST_FAILED.format(exc=exc)) from exc


async def send_usdt_transfer(
    client: FragmentClient,
    destination: str,
    usdt_amount: int,
    forward_payload: str | None = None,
    ton_for_gas: int = 50_000_000,
) -> UsdtTransferResult:
    """Send a direct USDT (TON jetton) transfer on-chain using ToncenterClient.

    Args:
        client: Authenticated :class:`FragmentClient` instance (seed and wallet_version used).
        destination: Recipient TON address (any format, e.g. ``"UQ..."``).
        usdt_amount: Amount in USDT base units (6 decimals; 1 USDT = 1 000 000).
        forward_payload: Optional comment forwarded to the recipient with the transfer notification.
        ton_for_gas: TON attached for gas in nanotons. Defaults to ``50_000_000`` (0.05 TON).

    Returns:
        :class:`UsdtTransferResult` with ``transaction_id``, ``destination``, and ``amount``.

    Raises:
        TransactionError: If the transaction fails to broadcast.
    """
    try:
        async with ToncenterClient(network=NetworkGlobalID.MAINNET) as ton:
            wallet_cls = WALLET_CLASSES[client.wallet_version]
            wallet, _, _, _ = wallet_cls.from_mnemonic(client=ton, mnemonic=client.seed)
            result = await wallet.transfer_message(
                JettonTransferBuilder(
                    destination=Address(destination),
                    jetton_amount=usdt_amount,
                    jetton_master_address=Address(USDT_TON_MASTER_ADDRESS),
                    forward_payload=forward_payload,
                    forward_amount=1,
                    amount=ton_for_gas,
                )
            )
            return UsdtTransferResult(
                transaction_id=str(result.normalized_hash),
                destination=destination,
                amount=usdt_amount,
            )
    except (TransactionError, WalletError):
        raise
    except Exception as exc:
        raise TransactionError(TransactionError.BROADCAST_FAILED.format(exc=exc)) from exc
