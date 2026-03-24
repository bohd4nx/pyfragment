from dataclasses import dataclass


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


@dataclass
class LoginCodeResult:
    """Result of :meth:`FragmentClient.get_login_code`."""

    number: str
    code: str | None
    active_sessions: int

    def __repr__(self) -> str:
        code_str = f"'{self.code}'" if self.code else "None"
        return f"LoginCodeResult(number='{self.number}', code={code_str}, active_sessions={self.active_sessions})"


@dataclass
class AdsRechargeResult:
    """Result of a successful self-recharge of Telegram Ads balance."""

    transaction_id: str
    amount: int

    def __repr__(self) -> str:
        return f"AdsRechargeResult(amount={self.amount} TON, tx='{self.transaction_id}')"


@dataclass
class TerminateSessionsResult:
    """Result of :meth:`FragmentClient.terminate_sessions`."""

    number: str
    message: str | None

    def __repr__(self) -> str:
        return f"TerminateSessionsResult(number='{self.number}', message={self.message!r})"


__all__ = [
    "AdsRechargeResult",
    "AdsTopupResult",
    "LoginCodeResult",
    "PremiumGiveawayResult",
    "PremiumResult",
    "StarsGiveawayResult",
    "StarsResult",
    "TerminateSessionsResult",
    "WalletInfo",
]
