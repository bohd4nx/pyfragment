from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CookieResult:
    """Result returned by :func:`~pyfragment.utils.get_cookies_from_browser`.

    Attributes:
        cookies: Dict with the four required Fragment cookie keys.
        expires: Expiry of the ``stel_ssid`` session cookie in ISO 8601 format (UTC),
            or ``None`` for session cookies.
    """

    cookies: dict[str, str]
    expires: str | None

    def __repr__(self) -> str:
        return f"CookieResult(expires={self.expires!r})"


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


@dataclass
class UsernamesResult:
    """Result of :meth:`FragmentClient.search_usernames`.

    Each dict in ``items`` has the keys:

    - ``slug`` — URL path (e.g. ``"username/durov"``).
    - ``name`` — display value (e.g. ``"@durov"``).
    - ``status`` — human-readable Fragment label (e.g. ``"On auction"``, ``"For sale"``).
    - ``price`` — price in TON formatted to two decimal places (e.g. ``"7.00"``), or ``None``.
    - ``date`` — ISO 8601 datetime: auction end date, sale date, or listing date, or ``None``.

    Use ``next_offset_id`` to paginate to the next page of results.
    """

    items: list[dict[str, Any]]
    next_offset_id: str | None

    def __repr__(self) -> str:
        return f"UsernamesResult(items={len(self.items)}, next_offset_id={self.next_offset_id!r})"


@dataclass
class NumbersResult:
    """Result of :meth:`FragmentClient.search_numbers`.

    Each dict in ``items`` has the keys:

    - ``slug`` — URL path (e.g. ``"number/8880000111"``).
    - ``name`` — display value (e.g. ``"+888 0000 111"``).
    - ``status`` — human-readable Fragment label (e.g. ``"On auction"``, ``"For sale"``).
    - ``price`` — price in TON formatted to two decimal places (e.g. ``"7.00"``), or ``None``.
    - ``date`` — ISO 8601 datetime: auction end date, sale date, or listing date, or ``None``.

    Use ``next_offset_id`` to paginate to the next page of results.
    """

    items: list[dict[str, Any]]
    next_offset_id: str | None

    def __repr__(self) -> str:
        return f"NumbersResult(items={len(self.items)}, next_offset_id={self.next_offset_id!r})"


@dataclass
class GiftsResult:
    """Result of :meth:`FragmentClient.search_gifts`.

    Each dict in ``items`` has the keys:

    - ``slug`` — URL path (e.g. ``"gift/plushpepe-1821"``).
    - ``name`` — display name with number (e.g. ``"Plush Pepe #1821"``).
    - ``status`` — human-readable Fragment label (e.g. ``"Sold"``, ``"For sale"``).
    - ``price`` — price in TON formatted to two decimal places (e.g. ``"88888.00"``), or ``None``.
    - ``date`` — ISO 8601 datetime of the sale/listing, or ``None``.

    Use ``next_offset`` to paginate to the next page of results.
    """

    items: list[dict[str, Any]]
    next_offset: int | None

    def __repr__(self) -> str:
        return f"GiftsResult(items={len(self.items)}, next_offset={self.next_offset!r})"


__all__ = [
    "AdsRechargeResult",
    "AdsTopupResult",
    "GiftsResult",
    "LoginCodeResult",
    "NumbersResult",
    "PremiumGiveawayResult",
    "PremiumResult",
    "StarsGiveawayResult",
    "StarsResult",
    "TerminateSessionsResult",
    "UsernamesResult",
    "WalletInfo",
]
