from dataclasses import dataclass

__all__ = ["AdsTopupResult", "PremiumGiveawayResult", "PremiumResult", "StarsGiveawayResult", "StarsResult", "WalletInfo"]


@dataclass
class WalletInfo:
    """Wallet state returned by :meth:`FragmentClient.get_wallet`."""

    address: str
    state: str
    balance: float

    def __repr__(self) -> str:
        return f"WalletInfo(address='{self.address}', state='{self.state}', balance={self.balance} TON)"


@dataclass
class PremiumResult:
    """Result of a successful Telegram Premium gift."""

    transaction_id: str
    username: str
    amount: int

    def __repr__(self) -> str:
        return f"PremiumResult(username='{self.username}', amount={self.amount} months, tx='{self.transaction_id}')"


@dataclass
class StarsResult:
    """Result of a successful Telegram Stars purchase."""

    transaction_id: str
    username: str
    amount: int

    def __repr__(self) -> str:
        return f"StarsResult(username='{self.username}', amount={self.amount} stars, tx='{self.transaction_id}')"


@dataclass
class AdsTopupResult:
    """Result of a successful Telegram Ads balance top-up."""

    transaction_id: str
    username: str
    amount: int

    def __repr__(self) -> str:
        return f"AdsTopupResult(username='{self.username}', amount={self.amount} TON, tx='{self.transaction_id}')"


@dataclass
class StarsGiveawayResult:
    """Result of a successful Telegram Stars giveaway."""

    transaction_id: str
    channel: str
    winners: int
    amount: int

    def __repr__(self) -> str:
        return (
            f"StarsGiveawayResult(channel='{self.channel}', winners={self.winners}, "
            f"amount={self.amount} stars per winner, tx='{self.transaction_id}')"
        )


@dataclass
class PremiumGiveawayResult:
    """Result of a successful Telegram Premium giveaway."""

    transaction_id: str
    channel: str
    winners: int
    amount: int

    def __repr__(self) -> str:
        return (
            f"PremiumGiveawayResult(channel='{self.channel}', winners={self.winners}, "
            f"amount={self.amount} months per winner, tx='{self.transaction_id}')"
        )
