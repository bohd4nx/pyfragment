from __future__ import annotations

import asyncio
import base64
import random
import ssl
from typing import TYPE_CHECKING, Any

from ton_core import Cell, NetworkGlobalID
from tonutils.clients import TonapiClient
from tonutils.exceptions import ProviderResponseError

from pyfragment.core.constants import WALLET_CLASSES
from pyfragment.domains.wallet.balance import check_ton_payment_balance, check_usdt_payment_balance
from pyfragment.exceptions import ParseError, TransactionError, WalletError
from pyfragment.models.enums import PaymentMethod

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


def clean_decode(payload: str) -> str | Cell:
    """Decode a base64-encoded BOC payload to a plain-text comment string."""
    s = payload.strip()
    if not s:
        return ""
    s += "=" * (-len(s) % 4)
    try:
        boc = base64.b64decode(s, altchars=b"-_", validate=True)
        cell = Cell.one_from_boc(boc)
        sl = cell.begin_parse()
        op = sl.load_uint(32)
        if op != 0:
            # Non-zero op code means this is a structured message (e.g. jetton transfer),
            # not a plain text comment — return the full cell as-is.
            return cell
        try:
            return sl.load_snake_string().strip()
        except UnicodeDecodeError:
            return cell
    except Exception as exc:
        raise ParseError(ParseError.UNPARSEABLE.format(context="payload decode", exc=exc)) from exc


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
            if payment_method == "ton":
                wallet.address.to_str(False, False)
                await check_ton_payment_balance(balance_ton, amount_ton, required_payment_amount)
            else:
                # USDT is withdrawn from the Fragment-linked wallet (transaction["from"]),
                # not from the signing seed wallet. Seed wallet only pays TON gas.
                fragment_wallet_address = transaction_data["transaction"].get("from", "")
                await check_usdt_payment_balance(balance_ton, required_payment_amount, ton, fragment_wallet_address)
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
