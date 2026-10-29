from __future__ import annotations

from dataclasses import dataclass

from pyfragment.domains.payments.models import PaymentResult


@dataclass
class AdsTopupResult(PaymentResult):
    username: str
    amount: int  # GRAM (ex TON)

    def __repr__(self) -> str:
        return (
            f"AdsTopupResult(username='{self.username}', amount={self.amount} GRAM (ex TON), "
            f"tx='{self.transaction_id}', confirmed={self.confirmed})"
        )


@dataclass
class AdsRechargeResult(PaymentResult):
    amount: int  # GRAM (ex TON)

    def __repr__(self) -> str:
        return f"AdsRechargeResult(amount={self.amount} GRAM (ex TON), tx='{self.transaction_id}', confirmed={self.confirmed})"
