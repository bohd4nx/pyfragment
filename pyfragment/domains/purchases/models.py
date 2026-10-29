from __future__ import annotations

from dataclasses import dataclass

from pyfragment.domains.payments.models import PaymentResult


@dataclass
class PremiumResult(PaymentResult):
    username: str
    amount: int  # months

    def __repr__(self) -> str:
        return (
            f"PremiumResult(username='{self.username}', amount={self.amount} months, "
            f"tx='{self.transaction_id}', confirmed={self.confirmed})"
        )


@dataclass
class StarsResult(PaymentResult):
    username: str
    amount: int  # stars

    def __repr__(self) -> str:
        return (
            f"StarsResult(username='{self.username}', amount={self.amount} stars, "
            f"tx='{self.transaction_id}', confirmed={self.confirmed})"
        )
