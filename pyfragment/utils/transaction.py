from __future__ import annotations

import time
from collections.abc import Iterable
from typing import Any

from ton_core import Address

from pyfragment.constants.chain import MESSAGE_TTL
from pyfragment.exceptions import TransactionError


def extract_message(transaction_data: dict[str, Any]) -> dict[str, Any]:
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


def unsigned_int(raw: object) -> int:
    """A non-negative integer field of Fragment's transaction (sent as a number or a digit string)."""
    if isinstance(raw, bool) or not isinstance(raw, (int, str)) or not str(raw).isdigit():
        raise TransactionError(TransactionError.INVALID_PAYLOAD)
    return int(raw)


def parse_destination(message: dict[str, Any]) -> Address:
    # An Address object, never a string: tonutils resolves strings containing a dot as .ton/.t.me domains.
    try:
        return Address(str(message["address"]))
    except Exception as exc:
        raise TransactionError(TransactionError.INVALID_PAYLOAD) from exc


def deadline(transaction_data: dict[str, Any]) -> int | None:
    """Fragment's own ``validUntil`` for the invoice, or ``None`` when it states none.

    Paying after it would pay an invoice Fragment may no longer honor, so an invoice that is already past it is refused.
    """
    raw = transaction_data["transaction"].get("validUntil")
    if raw is None:
        return None
    valid_until = unsigned_int(raw)
    if valid_until <= time.time():
        raise TransactionError.expired(valid_until)
    return valid_until


def signing_expiry(deadlines: Iterable[int | None], now: float) -> int:
    """When a transfer signed ``now`` stops being valid: ``MESSAGE_TTL`` seconds on, or at the earliest deadline."""
    return min([int(now) + MESSAGE_TTL, *(d for d in deadlines if d is not None)])
