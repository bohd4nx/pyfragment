from __future__ import annotations


class FragmentError(Exception):
    """Base exception for all pyfragment library errors."""


class ClientError(FragmentError):
    """Raised for client configuration and setup issues (bad params, invalid cookies)."""


class ConfigurationError(ClientError):
    """Raised when required client parameters are missing or invalid."""

    MISSING_VARS = "Missing required parameter(s): {keys}."
    UNSUPPORTED_VERSION = "Unsupported wallet_version '{version}'. Must be one of: {supported}."
    INVALID_MNEMONIC = "Invalid mnemonic: expected 12, 18, or 24 words, got {count}."
    INVALID_API_KEY = (
        "Invalid Tonapi API key: expected at least 68 characters, got {length}. Generate a key at https://tonconsole.com."
    )
    INVALID_MONTHS = "Invalid Premium duration: choose 3, 6, or 12 months."
    INVALID_STARS_AMOUNT = "Invalid Stars amount: must be an integer between 50 and 1 000 000."
    INVALID_TON_AMOUNT = "Invalid TON amount: must be an integer between 1 and 1 000 000 000."
    INVALID_USERNAME = (
        "Invalid username '{username}'. "
        "Must be 5–32 characters and contain only letters (A–Z, a–z), digits (0–9), or underscores (_)."
    )
    INVALID_WINNERS_STARS = "Invalid winners count: must be an integer between 1 and 5."
    INVALID_WINNERS_PREMIUM = "Invalid winners count: must be an integer between 1 and 24 000."
    INVALID_STARS_PER_WINNER = "Invalid Stars per winner: must be an integer between 500 and 1 000 000."


class CookieError(ClientError):
    """Raised when cookies are unreadable or missing required fields."""

    READ_FAILED = "Failed to parse cookies — expected a JSON string or a dict, got: {exc}"
    MISSING_KEYS = (
        "Fragment cookies are missing or empty for key(s): {keys}. "
        "Open fragment.com in your browser, log in, and copy fresh cookies."
    )
    UNSUPPORTED_BROWSER = "Unsupported browser: '{browser}'. Supported: {supported}."
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

    NO_REQUEST_ID = (
        "Fragment did not return a request ID for '{context}'. "
        "Your session may have expired — log in to fragment.com and refresh your cookies."
    )


class FragmentPageError(FragmentAPIError):
    """Raised when the Fragment page cannot be fetched or the API hash is not found."""

    BAD_STATUS = (
        "Fragment returned HTTP {status} when loading {url}. "
        "Your cookies may be invalid or expired — log in to fragment.com and refresh them."
    )
    NOT_FOUND = (
        "Could not extract the API hash from {url}. "
        "The page structure may have changed, or you are not logged in — refresh your cookies."
    )


class UserNotFoundError(FragmentAPIError):
    """Raised when the target Telegram user is not found on Fragment."""

    NOT_FOUND = (
        "Telegram user '{username}' was not found on Fragment. Double-check the username and make sure the account exists."
    )


class AnonymousNumberError(FragmentAPIError):
    """Raised for Fragment anonymous number API failures."""

    NOT_OWNED = "Number '{number}' is not associated with your Fragment account or has no active sessions to terminate."
    TERMINATE_FAILED = "Failed to terminate sessions for '{number}': {error}"


class TransactionError(FragmentAPIError):
    """Raised when a TON transaction fails to build or broadcast."""

    INVALID_PAYLOAD = (
        "Fragment returned an invalid transaction payload — 'transaction.messages' is missing or empty in the API response."
    )
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

    LOW_BALANCE = (
        "Insufficient TON balance: {balance:.4f} TON available, {required:.4f} TON required "
        "(transaction amount + {gas:.3f} TON gas reserve)."
    )
    BALANCE_CHECK_FAILED = "Failed to fetch wallet balance: {exc}"
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
    "UserNotFoundError",
    "TransactionError",
    "ParseError",
    "VerificationError",
    "OperationError",
    "WalletError",
    "UnexpectedError",
]
