"""Sign a Fragment transaction once, send exactly that message, and wait until the chain says whether it paid.

A signed message expires: once its ``valid_until`` has passed without it reaching the chain, it never will. So whether a
transfer paid is settled by looking for it on-chain until then, never by the provider's answer to the send. A transfer
is never signed twice: that would be a second, independent payment.
"""

from __future__ import annotations

import asyncio
import logging
import ssl
import time
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

import tonutils.exceptions
from ton_core import Address, normalize_hash
from tonutils.contracts.wallet import TONTransferBuilder
from tonutils.exceptions import ProviderResponseError

from pyfragment.constants import LANDING_GRACE, LANDING_POLL_INTERVAL, MESSAGE_TTL, TRANSACTIONS_PAGE_SIZE
from pyfragment.domains.wallet.balance import check_payment_balance
from pyfragment.domains.wallet.models import TransferIntent
from pyfragment.domains.wallet.payload import body_comment, decode_boc
from pyfragment.domains.wallet.wallet import provider_error
from pyfragment.enums import PaymentMethod
from pyfragment.exceptions import BroadcastError, ProviderError, TransactionError

if TYPE_CHECKING:
    from decimal import Decimal

    from pyfragment.client import FragmentClient


logger = logging.getLogger(__name__)


def _succeeded(tx: Any) -> bool:
    # Wallets send with "ignore errors": a transfer the wallet can't afford is skipped silently while the tx
    # succeeds and seqno advances. Both outmsg_cnt > 0 and skipped_actions == 0 must hold.
    d = tx.description
    if getattr(d, "aborted", True):
        return False
    compute = getattr(d, "compute_ph", None)
    action = getattr(d, "action", None)
    return (
        compute is not None
        and bool(compute.success)
        and action is not None
        and action.success
        and action.skipped_actions == 0
        and tx.outmsg_cnt > 0
    )


async def _find_transfer_by_lt(
    client: FragmentClient,
    *,
    msg_hash: str,
    last_lt: int,
) -> bool | None:
    """Scan the wallet's history for ``msg_hash``, stopping at ``last_lt``.

    Returns ``True`` (found, succeeded), ``False`` (found, failed), or ``None`` (not yet on-chain).
    Uses logical time as the lower bound to eliminate clock-skew false negatives.
    """
    ton_wallet = client.ton_wallet
    low_hash = msg_hash.lower()
    try:
        ton = await ton_wallet.ton()
        address = ton_wallet.wallet().address
        from_lt: int | None = None
        while True:
            page = await ton.get_transactions(address, limit=TRANSACTIONS_PAGE_SIZE, from_lt=from_lt)
            for tx in page:
                if tx.lt <= last_lt:
                    return None
                in_msg = tx.in_msg
                if in_msg is not None and in_msg.is_external and normalize_hash(in_msg) == low_hash:
                    return _succeeded(tx)
            if len(page) < TRANSACTIONS_PAGE_SIZE:
                return None
            from_lt = page[-1].lt - 1
    except Exception as exc:
        raise provider_error(ProviderError.TRANSFER_LOOKUP_FAILED, exc) from exc


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


def _broadcast_error(
    template: str, intent: TransferIntent, retryable: bool, exc: BaseException | None = None
) -> BroadcastError:
    message = template.format(msg_hash=intent.msg_hash, exc=exc)
    cause: BaseException | None = exc
    while cause is not None:
        if isinstance(cause, ssl.SSLError):
            message += BroadcastError.SSL_HINT
            break
        cause = cause.__cause__ or cause.__context__
    return BroadcastError(message, intent, retryable=retryable)


async def _send_message(ton: Any, boc_hex: str, valid_until: int) -> Exception | None:
    """Send the signed message, retrying once on a 429 while the message is still valid.

    Returns the exception if the send ultimately failed, or ``None`` on success. The chain decides whether the message
    landed regardless: toncenter answers 500 to some sends that went through.
    """
    try:
        await ton.send_message(boc_hex)
        return None
    except ProviderResponseError as exc:
        if exc.code == HTTPStatus.TOO_MANY_REQUESTS and time.time() < valid_until:
            await asyncio.sleep(1)
            try:
                await ton.send_message(boc_hex)
                return None
            except Exception as retry_exc:
                return retry_exc
        return exc
    except Exception as exc:
        return exc


async def _wait_until_landed(
    client: FragmentClient, intent: TransferIntent, last_lt: int, send_error: Exception | None
) -> None:
    """Poll the wallet's history until the transfer shows up, or until it can no longer land.

    Uses ``last_lt`` (the wallet's logical time before signing) as the lower bound, which avoids false negatives from
    local-clock skew. Raises ``BroadcastError``: retryable if the transfer certainly paid nothing, not retryable if
    that couldn't be determined.
    """
    deadline = intent.valid_until + LANDING_GRACE
    while True:
        try:
            found = await _find_transfer_by_lt(client, msg_hash=intent.msg_hash, last_lt=last_lt)
        except ProviderError as exc:
            if time.time() >= deadline:
                logger.warning("Couldn't check whether transfer %s paid: %s", intent.msg_hash, exc)
                raise _broadcast_error(BroadcastError.UNKNOWN, intent, retryable=False, exc=exc) from exc
            found = None
        if found is not None:
            if not found:
                raise _broadcast_error(BroadcastError.FAILED, intent, retryable=True)
            logger.debug("Transfer %s confirmed on-chain", intent.msg_hash)
            return
        if time.time() >= deadline:
            template = BroadcastError.NOT_SENT if send_error is not None else BroadcastError.NOT_LANDED
            raise _broadcast_error(template, intent, retryable=True, exc=send_error) from send_error
        await asyncio.sleep(LANDING_POLL_INTERVAL)


async def process_transaction(
    client: FragmentClient,
    transaction_data: dict[str, Any],
    payment_method: PaymentMethod = PaymentMethod.GRAM,
    required_payment_amount: Decimal | None = None,
    req_id: str | None = None,
) -> TransferIntent:
    """Sign and send a Fragment transaction with the seeded GRAM (ex TON) wallet, and wait until it has paid.

    Args:
        client: Authenticated `FragmentClient` instance.
        transaction_data: Raw Fragment transaction payload returned by the API.
        payment_method: Payment currency to use for the purchase flow.
        required_payment_amount: Amount from Fragment's invoice, in the payment currency.
        req_id: Fragment's invoice id, passed on to the ``on_transfer_prepared`` hook.

    Returns:
        The paid transfer: its normalized message hash, the signed boc (what Fragment's own `confirm_method`, e.g.
        confirmReq, expects) and the payment details.

    Raises:
        BroadcastError: Once the message is signed, if it didn't pay (``retryable``) or that couldn't be checked.
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
        last_lt: int = onchain.last_transaction_lt or 0
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

        try:
            if client.on_transfer_prepared is not None:
                await client.on_transfer_prepared(intent)
            ton = await ton_wallet.ton()
        except Exception as exc:
            raise _broadcast_error(BroadcastError.NOT_SENT, intent, retryable=True, exc=exc) from exc

        send_error = await _send_message(ton, external.as_hex, valid_until)
        await _wait_until_landed(client, intent, last_lt, send_error)
        return intent
