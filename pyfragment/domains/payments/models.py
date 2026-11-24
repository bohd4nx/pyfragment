from __future__ import annotations

from dataclasses import dataclass


@dataclass(kw_only=True)
class PaymentResult:
    """What every purchase reports about the transfer that paid it."""

    transaction_id: str  # hash of the signed message, to look the transfer up on-chain
    confirmed: bool  # Fragment acknowledged it in time (best effort, not proof)
    comment: str | None  # Fragment's payment reference sent with the transfer
    boc: str  # the signed external message, base64
