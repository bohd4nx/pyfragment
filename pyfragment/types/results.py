import time
from dataclasses import dataclass, field

__all__ = ["AdsTopupResult", "PremiumResult", "StarsResult", "WalletInfo"]


@dataclass
class WalletInfo:
    """Wallet state returned by :meth:`FragmentClient.get_wallet`."""

    address: str
    state: str
    balance: float


@dataclass
class PremiumResult:
    """Result of a successful Telegram Premium gift."""

    transaction_id: str
    username: str
    months: int
    timestamp: int = field(default_factory=lambda: int(time.time()))


@dataclass
class StarsResult:
    """Result of a successful Telegram Stars purchase."""

    transaction_id: str
    username: str
    stars: int
    timestamp: int = field(default_factory=lambda: int(time.time()))


@dataclass
class AdsTopupResult:
    """Result of a successful Telegram Ads balance top-up."""

    transaction_id: str
    username: str
    amount: int
    timestamp: int = field(default_factory=lambda: int(time.time()))
