from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AdsTopupResult:
    transaction_id: str
    username: str
    amount: int

    def __repr__(self) -> str:
        return f"AdsTopupResult(username='{self.username}', amount={self.amount} GRAM (ex TON), tx='{self.transaction_id}')"


@dataclass
class AdsRechargeResult:
    transaction_id: str
    amount: int

    def __repr__(self) -> str:
        return f"AdsRechargeResult(amount={self.amount} GRAM (ex TON), tx='{self.transaction_id}')"


__all__ = ["AdsRechargeResult", "AdsTopupResult"]
