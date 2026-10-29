from __future__ import annotations

from dataclasses import dataclass

from pyfragment.domains.payments.models import PaymentResult


@dataclass
class StarsGiveawayResult(PaymentResult):
    channel: str
    winners: int
    amount: int  # stars per winner

    def __repr__(self) -> str:
        return (
            f"StarsGiveawayResult(channel='{self.channel}', winners={self.winners}, "
            f"amount={self.amount} stars per winner, tx='{self.transaction_id}', confirmed={self.confirmed})"
        )


@dataclass
class PremiumGiveawayResult(PaymentResult):
    channel: str
    winners: int
    amount: int  # months per winner

    def __repr__(self) -> str:
        return (
            f"PremiumGiveawayResult(channel='{self.channel}', winners={self.winners}, "
            f"amount={self.amount} months per winner, tx='{self.transaction_id}', confirmed={self.confirmed})"
        )
