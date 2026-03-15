class FragmentError(Exception):
    """Base exception for all pyfragment library errors."""


class ClientError(FragmentError):
    """Raised for client configuration and setup issues (bad params, invalid cookies)."""


class ConfigurationError(ClientError):
    """Raised when required client parameters are missing or invalid."""

    MISSING_VARS = "Missing required parameter(s): {keys}."
    UNSUPPORTED_VERSION = "Unsupported wallet_version '{version}'. Must be one of: {supported}."
    INVALID_MNEMONIC = "Invalid mnemonic: got {count} words, expected 12, 18, or 24."
    INVALID_MONTHS = "Invalid duration. Choose 3, 6, or 12 months."
    INVALID_STARS_AMOUNT = "Amount must be an integer between 50 and 1 000 000 stars."
    INVALID_TON_AMOUNT = "Amount must be an integer between 1 and 1 000 000 000 TON."


class CookieError(ClientError):
    """Raised when cookies are unreadable or missing required fields."""

    READ_FAILED = "Failed to parse cookies: {exc}"
    MISSING_KEYS = (
        "Cookies are missing or have empty values for: {keys}. " "Open Fragment.com in your browser and copy fresh cookies."
    )


class FragmentAPIError(FragmentError):
    """Raised for errors returned by Fragment's API responses."""

    NO_REQUEST_ID = (
        "Fragment did not return a request ID for '{context}'. " "The session may have expired — refresh your cookies."
    )


class FragmentPageError(FragmentAPIError):
    """Raised when the Fragment page cannot be fetched or the API hash is not found."""

    BAD_STATUS = "Fragment returned HTTP {status} for {url}. " "Check that your cookies are valid and not expired."
    NOT_FOUND = (
        "Fragment hash not found in the page source of {url}. " "The page structure may have changed or you are not logged in."
    )


class UserNotFoundError(FragmentAPIError):
    """Raised when the target Telegram user is not found on Fragment."""

    NOT_FOUND = (
        "Telegram user '{username}' was not found on Fragment. " "Make sure the username is correct and the account exists."
    )


class TransactionError(FragmentAPIError):
    """Raised when a TON transaction fails to build or broadcast."""

    INVALID_PAYLOAD = (
        "Fragment returned an invalid transaction payload. " "The API response is missing expected 'transaction.messages' data."
    )
    BROADCAST_FAILED = "Transaction broadcast failed: {exc}"


class ParseError(FragmentAPIError):
    """Raised when a Fragment API response or payload cannot be parsed."""

    UNPARSEABLE = "Fragment API returned an unparseable response for '{context}': {exc}"


class VerificationError(FragmentAPIError):
    """Raised when Fragment requires KYC verification before proceeding."""

    KYC_REQUIRED = "Fragment requires identity (KYC) verification. " "Complete it at https://fragment.com/my/profile and retry."


class OperationError(FragmentError):
    """Raised for runtime operation failures unrelated to Fragment's API."""


class WalletError(OperationError):
    """Raised for TON wallet issues (connection, balance, account info)."""

    LOW_BALANCE = "TON wallet balance is too low: {balance:.4f} TON available, {required:.4f} TON required."
    BALANCE_CHECK_FAILED = "Wallet balance check failed: {exc}"
    ACCOUNT_INFO_FAILED = "Failed to retrieve wallet account info: {exc}"
    WALLET_INFO_FAILED = "Failed to retrieve wallet info: {exc}"


class UnexpectedError(OperationError):
    """Raised when an unexpected error occurs during an API call."""

    UNEXPECTED = "An unexpected error occurred: {exc}"


__all__ = [
    "FragmentError",
    "ClientError",
    "ConfigurationError",
    "CookieError",
    "FragmentAPIError",
    "FragmentPageError",
    "UserNotFoundError",
    "TransactionError",
    "ParseError",
    "VerificationError",
    "OperationError",
    "WalletError",
    "UnexpectedError",
]
