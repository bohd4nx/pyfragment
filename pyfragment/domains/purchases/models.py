from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PremiumResult:
    transaction_id: str
    username: str
    amount: int

    def __repr__(self) -> str:
        return f"PremiumResult(username='{self.username}', amount={self.amount} months, tx='{self.transaction_id}')"


@dataclass
class StarsResult:
    transaction_id: str
    username: str
    amount: int

    def __repr__(self) -> str:
        return f"StarsResult(username='{self.username}', amount={self.amount} stars, tx='{self.transaction_id}')"
