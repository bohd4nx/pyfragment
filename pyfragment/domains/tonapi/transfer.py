from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ton_core import Address, NetworkGlobalID
from tonutils.clients import ToncenterClient
from tonutils.contracts import JettonTransferBuilder, TONTransferBuilder

from pyfragment.core.constants import USDT_TON_MASTER_ADDRESS, WALLET_CLASSES
from pyfragment.exceptions import TransactionError, WalletError
from pyfragment.models.wallet import TonTransferResult, UsdtTransferResult

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


logger = logging.getLogger(__name__)


async def send_ton_transfer(
    client: FragmentClient,
    destination: str,
    amount: int,
    body: str | None = None,
) -> TonTransferResult:
    """Send a direct TON transfer from the seeded wallet.

    Args:
        client: Authenticated `FragmentClient` instance.
        destination: Recipient address in any TON-compatible format.
        amount: Amount in nanotons.
        body: Optional on-chain comment.
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
        logger.exception(
            "Failed to send TON transfer to '%s' for %s nanotons",
            destination,
            amount,
        )
        raise TransactionError(TransactionError.BROADCAST_FAILED.format(exc=exc)) from exc


async def send_usdt_transfer(
    client: FragmentClient,
    destination: str,
    usdt_amount: int,
    forward_payload: str | None = None,
    ton_for_gas: int = 50_000_000,
) -> UsdtTransferResult:
    """Send a direct USDT transfer from the seeded wallet.

    Args:
        client: Authenticated `FragmentClient` instance.
        destination: Recipient address in any TON-compatible format.
        usdt_amount: Amount in USDT base units (6 decimals).
        forward_payload: Optional comment passed through to the recipient.
        ton_for_gas: TON attached for gas in nanotons.
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
        logger.exception(
            "Failed to send USDT transfer to '%s' for %s base units",
            destination,
            usdt_amount,
        )
        raise TransactionError(TransactionError.BROADCAST_FAILED.format(exc=exc)) from exc
