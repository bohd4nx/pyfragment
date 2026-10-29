from __future__ import annotations

from dataclasses import dataclass


@dataclass(kw_only=True)
class PaymentResult:
    """What every purchase reports about the transfer that paid it."""

    transaction_id: str  # normalized hash of the signed message, for find_transfer(msg_hash=...)
    confirmed: bool  # Fragment acknowledged the payment within confirm_timeout (best effort, not proof of payment)
    comment: str | None  # Fragment's payment reference sent with the transfer
    boc: str  # the signed external message, base64
