from __future__ import annotations

from pyfragment.core.constants.limits import (
    MNEMONIC_WORD_COUNTS_VALID,
    PREMIUM_MONTHS_VALID,
    PREMIUM_WINNERS_MAX,
    PREMIUM_WINNERS_MIN,
    STARS_GIVEAWAY_MAX,
    STARS_GIVEAWAY_MIN,
    STARS_PURCHASE_MAX,
    STARS_PURCHASE_MIN,
    STARS_WINNERS_MAX,
    STARS_WINNERS_MIN,
    TON_TOPUP_MAX,
    TON_TOPUP_MIN,
    TONAPI_KEY_MIN_LENGTH,
)


class FragmentError(Exception):
    """Base exception for all pyfragment errors."""


class ClientError(FragmentError):
    """Raised for client configuration and setup issues."""


class ConfigurationError(ClientError):
    """Raised when required client parameters are missing or invalid."""

    MISSING_VARS = "Missing required parameter(s): {keys}."
    UNSUPPORTED_VERSION = "Unsupported wallet version '{version}'. Supported values: {supported}."
    INVALID_MNEMONIC = f"Invalid mnemonic phrase: expected {', '.join(str(n) for n in sorted(MNEMONIC_WORD_COUNTS_VALID))} words, got {{count}}."
    INVALID_API_KEY = (
        f"Invalid Tonapi API key: expected at least {TONAPI_KEY_MIN_LENGTH} characters, got {{length}}. "
        "Get a key at https://tonconsole.com."
    )
    INVALID_MONTHS = f"Invalid Premium duration: choose {', '.join(str(m) for m in sorted(PREMIUM_MONTHS_VALID))} months."
    INVALID_STARS_AMOUNT = (
        f"Invalid Stars amount: must be an integer between {STARS_PURCHASE_MIN:,} and {STARS_PURCHASE_MAX:,}."
    )
    INVALID_TON_AMOUNT = f"Invalid TON amount: must be an integer between {TON_TOPUP_MIN:,} and {TON_TOPUP_MAX:,}."
    INVALID_USERNAME = (
        "Invalid username '{username}'. "
        "Must be 5-32 characters and contain only letters (A-Z, a-z), digits (0-9), or underscores (_)."
    )
    INVALID_WINNERS_STARS = (
        f"Invalid winners count: must be an integer between {STARS_WINNERS_MIN:,} and {STARS_WINNERS_MAX:,}."
    )
    INVALID_WINNERS_PREMIUM = (
        f"Invalid winners count: must be an integer between {PREMIUM_WINNERS_MIN:,} and {PREMIUM_WINNERS_MAX:,}."
    )
    INVALID_STARS_PER_WINNER = (
        f"Invalid Stars per winner: must be an integer between {STARS_GIVEAWAY_MIN:,} and {STARS_GIVEAWAY_MAX:,}."
    )
    INVALID_PAYMENT_METHOD = "Invalid payment method '{method}'. Supported values: {supported}."


class CookieError(ClientError):
    """Raised when cookies are unreadable or missing required fields."""

    READ_FAILED = "Failed to parse cookies: expected a JSON string or a dict, got {exc}."
    MISSING_KEYS = (
        "Fragment cookies are missing or empty for key(s): {keys}. "
        "Open fragment.com in your browser, log in, and copy fresh cookies."
    )
    UNSUPPORTED_BROWSER = "Unsupported browser '{browser}'. Supported values: {supported}."
    BROWSER_READ_FAILED = (
        "Failed to read {browser} cookies: {exc}. Make sure {browser} is installed and you are logged in to {url}."
    )
    MISSING_BROWSER_KEYS = (
        "Fragment cookies not found in {browser}: {keys}. "
        "Make sure you are logged in to {url} and have connected your TON wallet in {browser}."
    )
    EXPIRED = "Fragment session cookie expired at {expires}. Log in to fragment.com in your browser and extract fresh cookies."


class FragmentAPIError(FragmentError):
    """Raised for errors returned by Fragment's API responses."""

    NO_REQUEST_ID = "Fragment did not return a request ID for '{context}'. Your session may have expired. Refresh your cookies and try again."


class FragmentPageError(FragmentAPIError):
    """Raised when the Fragment page cannot be fetched or the API hash is not found."""

    BAD_STATUS = "Fragment returned HTTP {status} when loading {url}. Your cookies may be invalid or expired. Refresh them and try again."
    NOT_FOUND = "Could not extract the API hash from {url}. The page structure may have changed, or you may not be logged in. Refresh your cookies."


class UserNotFoundError(FragmentAPIError):
    """Raised when the target Telegram user is not found on Fragment."""

    NOT_FOUND = (
        "Telegram user '{username}' was not found on Fragment. Double-check the username and make sure the account exists."
    )


class AlreadySubscribedError(FragmentAPIError):
    """Raised when trying to gift Premium to a user who already has an active subscription."""

    PREMIUM_ACTIVE = "This account is already subscribed to Telegram Premium."


class AnonymousNumberError(FragmentAPIError):
    """Raised for Fragment anonymous number API failures."""

    NOT_OWNED = "Number '{number}' is not associated with your Fragment account or has no active sessions to terminate."
    TERMINATE_FAILED = "Failed to terminate sessions for '{number}': {error}"


class TransactionError(FragmentAPIError):
    """Raised when a TON transaction fails to build or broadcast."""

    INVALID_PAYLOAD = "Fragment returned an invalid transaction payload: 'transaction.messages' is missing or empty."
    BROADCAST_FAILED = "Transaction broadcast failed: {exc}"
    BROADCAST_FAILED_SSL = (
        "Transaction broadcast failed due to an SSL certificate error: {exc}\n"
        "This usually means your system's CA bundle is missing or outdated.\n"
        "Fix: run `pip install --upgrade certifi` and retry. "
        "On macOS you may also need to run the 'Install Certificates.command' "
        "located in your Python installation folder."
    )
    DUPLICATE_SEQNO = (
        "Transaction broadcast failed: the TON wallet rejected the message "
        "because a previous transaction with the same sequence number (seqno) "
        "is still pending confirmation on-chain.\n"
        "Wait a few seconds for the previous transaction to confirm, then retry."
    )


class ParseError(FragmentAPIError):
    """Raised when a Fragment API response or payload cannot be parsed."""

    UNPARSEABLE = "Failed to parse the Fragment API response for '{context}': {exc}"


class VerificationError(FragmentAPIError):
    """Raised when Fragment requires KYC verification before proceeding."""

    KYC_REQUIRED = (
        "Fragment requires identity verification (KYC) before this action can be completed. "
        "Complete verification at https://fragment.com/my/profile and retry."
    )


class OperationError(FragmentError):
    """Raised for runtime operation failures unrelated to Fragment's API."""


class WalletError(OperationError):
    """Raised for TON wallet issues (connection, balance, account info)."""

    LOW_TON_BALANCE = "Insufficient TON balance: {balance:.4f} TON available, {required:.4f} TON required."
    LOW_USDT_BALANCE = "Insufficient USDT balance: {balance:.4f} USDT available, {required:.4f} USDT required."
    TON_BALANCE_CHECK_FAILED = "Failed to fetch TON balance: {exc}"
    USDT_BALANCE_CHECK_FAILED = "Failed to fetch USDT balance: {exc}"
    ACCOUNT_INFO_FAILED = "Failed to retrieve wallet account info from TON network: {exc}"
    WALLET_INFO_FAILED = "Failed to retrieve wallet info from TON network: {exc}"


class UnexpectedError(OperationError):
    """Raised when an unexpected error occurs during an API call."""

    UNEXPECTED = "An unexpected error occurred during the operation: {exc}"


__all__ = [
    "FragmentError",
    "ClientError",
    "ConfigurationError",
    "CookieError",
    "FragmentAPIError",
    "FragmentPageError",
    "AnonymousNumberError",
    "AlreadySubscribedError",
    "UserNotFoundError",
    "TransactionError",
    "ParseError",
    "VerificationError",
    "OperationError",
    "WalletError",
    "UnexpectedError",
]
