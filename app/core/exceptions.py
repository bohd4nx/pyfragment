__all__ = [
    "ConfigError",
    "CookiesError",
    "FragmentError",
    "HashFetchError",
    "RequestError",
    "TransactionError",
    "UserNotFoundError",
    "WalletError",
]


class FragmentError(Exception):
    """Base exception for all Fragment API errors."""


class ConfigError(FragmentError):
    """Raised when .env is missing or required keys are absent."""


class CookiesError(FragmentError):
    """Raised when cookies.json is missing, unreadable, or has empty required fields."""


class HashFetchError(FragmentError):
    """Raised when the Fragment API hash cannot be fetched from the page."""


class UserNotFoundError(FragmentError):
    """Raised when the target Telegram user is not found on Fragment."""


class WalletError(FragmentError):
    """Raised for TON wallet issues (connection, balance, account info)."""


class TransactionError(FragmentError):
    """Raised when a TON transaction fails to build or broadcast."""


class RequestError(FragmentError):
    """Raised when a Fragment API response cannot be parsed."""
