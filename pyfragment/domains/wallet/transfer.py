"""Sign a Fragment transaction once and send it; Fragment's confirmation API handles the outcome.

A signed message expires: once its ``valid_until`` has passed, the wallet won't accept it and nothing lands.
A transfer is never signed twice: that would create a second, independent payment.
"""

from __future__ import annotations

import asyncio
import logging
import time
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

import tonutils.exceptions
from ton_core import Address
from tonutils.contracts.wallet import TONTransferBuilder
from tonutils.exceptions import ProviderResponseError

from pyfragment.constants import MESSAGE_TTL
from pyfragment.domains.wallet.balance import check_payment_balance
from pyfragment.domains.wallet.models import TransferIntent
from pyfragment.domains.wallet.payload import body_comment, decode_boc
from pyfragment.domains.wallet.wallet import provider_error
from pyfragment.enums import PaymentMethod
from pyfragment.exceptions import ProviderError, TransactionError

if TYPE_CHECKING:
    from decimal import Decimal

    from pyfragment.client import FragmentClient


logger = logging.getLogger(__name__)


def _extract_message(transaction_data: dict[str, Any]) -> dict[str, Any]:
    """The one message of a Fragment transaction payload."""
    transaction = transaction_data.get("transaction")
    messages = transaction.get("messages") if isinstance(transaction, dict) else None
    if not messages or not isinstance(messages, list):
        raise TransactionError(TransactionError.INVALID_PAYLOAD)
    if len(messages) != 1:
        # Signing only the first one would pay part of the invoice and check the balance for that part only.
        raise TransactionError(TransactionError.MULTIPLE_MESSAGES.format(count=len(messages)))
    message: dict[str, Any] = messages[0]
    return message


def _unsigned_int(raw: object) -> int:
    """A non-negative integer field of Fragment's transaction (sent as a number or a digit string)."""
    if isinstance(raw, bool) or not isinstance(raw, (int, str)) or not str(raw).isdigit():
        raise TransactionError(TransactionError.INVALID_PAYLOAD)
    return int(raw)


def _parse_destination(message: dict[str, Any]) -> Address:
    # An Address object, never a string: tonutils resolves strings containing a dot as .ton/.t.me domains.
    try:
        return Address(str(message["address"]))
    except Exception as exc:
        raise TransactionError(TransactionError.INVALID_PAYLOAD) from exc


def _expiry(transaction_data: dict[str, Any]) -> int:
    """When the signed transfer expires: in ``MESSAGE_TTL`` seconds, or earlier if Fragment's own deadline is earlier.

    Paying after Fragment's ``validUntil`` would pay an invoice it may no longer honor, so that is refused outright.
    """
    now = int(time.time())
    raw = transaction_data["transaction"].get("validUntil")
    if raw is None:
        return now + MESSAGE_TTL
    valid_until = _unsigned_int(raw)
    if valid_until <= now:
        raise TransactionError(TransactionError.EXPIRED.format(valid_until=valid_until), retryable=True)
    return min(now + MESSAGE_TTL, valid_until)


async def _send_message(ton: Any, boc_hex: str, valid_until: int) -> None:
    """Send the signed message, retrying once on a 429 while the message is still valid.

    Send errors are logged but not raised: the chain decides whether the message landed, and Fragment's
    confirmation API reports the outcome. toncenter answers 500 to some sends that went through.
    """
    try:
        await ton.send_message(boc_hex)
    except ProviderResponseError as exc:
        if exc.code == HTTPStatus.TOO_MANY_REQUESTS and time.time() < valid_until:
            await asyncio.sleep(1)
            try:
                await ton.send_message(boc_hex)
            except Exception as retry_exc:
                logger.warning("Failed to send transfer (retry): %s", retry_exc)
        else:
            logger.warning("Failed to send transfer: %s", exc)
    except Exception as exc:
        logger.warning("Failed to send transfer: %s", exc)


async def process_transaction(
    client: FragmentClient,
    transaction_data: dict[str, Any],
    payment_method: PaymentMethod = PaymentMethod.GRAM,
    required_payment_amount: Decimal | None = None,
    req_id: str | None = None,
) -> TransferIntent:
    """Sign and send a Fragment transaction with the seeded GRAM (ex TON) wallet.

    Args:
        client: Authenticated `FragmentClient` instance.
        transaction_data: Raw Fragment transaction payload returned by the API.
        payment_method: Payment currency to use for the purchase flow.
        required_payment_amount: Amount from Fragment's invoice, in the payment currency.
        req_id: Fragment's invoice id, passed on to the ``on_transfer_prepared`` hook.

    Returns:
        The signed transfer: its normalized message hash, the signed boc and the payment details.
    """
    message = _extract_message(transaction_data)
    amount_nano = _unsigned_int(message.get("amount"))
    destination = _parse_destination(message)
    body = decode_boc(message.get("payload"))
    ton_wallet = client.ton_wallet

    async with ton_wallet.lock:
        onchain = await check_payment_balance(
            client,
            payment_method,
            amount_nano,
            required_payment_amount,
            transaction_data["transaction"].get("from", ""),
        )
        valid_until = _expiry(transaction_data)
        params = await ton_wallet.transfer_params(valid_until, state=onchain)
        try:
            external = await ton_wallet.wallet().build_external_message(
                [TONTransferBuilder(destination=destination, amount=amount_nano, body=body)], params
            )
        except tonutils.exceptions.ProviderError as exc:
            raise provider_error(ProviderError.WALLET_STATE_FAILED, exc) from exc

        intent = TransferIntent(
            msg_hash=str(external.normalized_hash),
            boc=external.as_b64,
            destination=str(message["address"]),
            amount_nano=amount_nano,
            comment=body_comment(body),
            payment_method=payment_method,
            req_id=req_id,
            valid_until=valid_until,
        )
        logger.debug("Signed transfer %s (valid_until=%d, amount=%d nano)", intent.msg_hash, valid_until, amount_nano)

        if client.on_transfer_prepared is not None:
            await client.on_transfer_prepared(intent)

        ton = await ton_wallet.ton()
        await _send_message(ton, external.as_hex, valid_until)
        return intent
