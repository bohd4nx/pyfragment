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
from pyfragment.domains.tonapi.account import check_ton_payment_balance, check_usdt_payment_balance
from pyfragment.exceptions import ParseError, TransactionError, WalletError
from pyfragment.models.enums import PaymentMethod

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


def clean_decode(payload: str) -> str | Cell:
    """Decode a base64 BOC comment from Fragment into text when possible.

    Some Fragment payloads are plain text comments, while others are structured
    TON messages such as jetton transfers. Non-text payloads are returned as a
    `Cell` so the caller can keep the raw binary structure.
    """
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
            # Non-zero op code means this is a structured TON message, not a plain text comment.
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
    """Sign and broadcast a Fragment transaction with the seeded TON wallet.

    Args:
        client: Authenticated `FragmentClient` instance.
        transaction_data: Raw Fragment transaction payload returned by the API.
        payment_method: Payment currency to use for the purchase flow.
        required_payment_amount: Optional amount returned by Fragment's init request.

    Returns:
        Normalized transaction hash string.
    """
    if "transaction" not in transaction_data or not transaction_data["transaction"].get("messages"):
        raise TransactionError(TransactionError.INVALID_PAYLOAD)

    message = transaction_data["transaction"]["messages"][0]
    amount_ton = int(message["amount"]) / 1_000_000_000

    async with TonapiClient(network=NetworkGlobalID.MAINNET, api_key=client.api_key) as ton:
        wallet_cls = WALLET_CLASSES[client.wallet_version]
        wallet, _, _, _ = wallet_cls.from_mnemonic(client=ton, mnemonic=client.seed)

        # Check balance first so we fail before trying to broadcast on-chain.
        try:
            await wallet.refresh()
            balance_ton = wallet.balance / 1_000_000_000
            if payment_method == "ton":
                wallet.address.to_str(False, False)
                await check_ton_payment_balance(balance_ton, amount_ton, required_payment_amount)
            else:
                # USDT is paid from the Fragment-linked wallet, not the signing wallet.
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
