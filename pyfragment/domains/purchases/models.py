from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from pyfragment.domains.payments.models import PaymentResult


@dataclass(frozen=True)
class StarsPackage:
    """One predefined Stars purchase option with current prices."""

    stars: int
    gram: Decimal
    usd: Decimal

    def __repr__(self) -> str:
        return f"StarsPackage(stars={self.stars}, gram={self.gram}, usd={self.usd})"


@dataclass(frozen=True)
class PremiumPackage:
    """One predefined Telegram Premium subscription option with current prices."""

    months: int
    gram: Decimal
    usd: Decimal

    def __repr__(self) -> str:
        return f"PremiumPackage(months={self.months}, gram={self.gram}, usd={self.usd})"


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
