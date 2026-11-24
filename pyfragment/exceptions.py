"""Exceptions raised by pyfragment.

``retryable`` means nothing was paid and repeating the call may succeed.
"""

from __future__ import annotations

from http import HTTPStatus

from tonutils.exceptions import ProviderResponseError

from pyfragment.constants.fragment import PROFILE_PAGE
from pyfragment.constants.limits import PREMIUM_MONTHS_VALID
from pyfragment.utils.money import numbers_in


class FragmentError(Exception):
    """Base exception for all pyfragment errors."""

    retryable: bool = False
    """Nothing was paid, and repeating the call may succeed (the cause looks transient)."""

    def __init__(self, message: str = "", *, retryable: bool | None = None) -> None:
        super().__init__(message)
        if retryable is not None:
            self.retryable = retryable


class ClientError(FragmentError):
    """Raised for client configuration and setup issues."""


class ConfigurationError(ClientError):
    """Raised when required client parameters are missing or invalid."""

    MISSING_VARS = "Missing required parameter(s): {keys}."
    UNSUPPORTED_VERSION = "Unsupported wallet version '{value}'. Supported values: {supported}."
    UNSUPPORTED_MNEMONIC_TYPE = "Unsupported mnemonic type '{value}'. Supported values: {supported}."
    INVALID_SEED = "Invalid seed phrase: {exc}"
    INVALID_CONFIRM_TIMEOUT = "Invalid confirm_timeout '{value}': must be a non-negative number of seconds."
    INVALID_MAX_BATCH = "Invalid max_batch '{value}': must be a positive whole number."
    UNSUPPORTED_PROVIDER = "Unsupported API provider '{value}'. Supported values: {supported}."
    TOO_MANY_WINNERS = (
        "Too many winners: a {amount:,} Stars package is split between at most {max:,} winners "
        "(at least {per_winner:,} Stars each)."
    )
    INVALID_MONTHS = f"Invalid Premium duration: choose {', '.join(str(m) for m in sorted(PREMIUM_MONTHS_VALID))} months."
    OUT_OF_RANGE = "Invalid {label}: must be an integer between {min:,} and {max:,}."
    INVALID_SORT = "Invalid sort order '{value}'. Supported values: {supported}."
    INVALID_FILTER = "Invalid filter '{value}'. Supported values: {supported}."
    INVALID_GIFT_ATTRIBUTE = "Invalid gift attribute '{value}'. Supported values: {supported}."
    INVALID_PAYMENT_METHOD = "Invalid payment method '{method}'. Supported values: {supported}."


class CookieError(ClientError):
    """Raised when cookies are unreadable or missing required fields."""

    READ_FAILED = "Failed to parse cookies: expected a JSON object or a dict, got {exc}."
    MISSING_KEYS = (
        "Fragment cookies are missing or empty for key(s): {keys}. "
        "Open fragment.com in your browser, log in, and copy fresh cookies."
    )


class FragmentAPIError(FragmentError):
    """Raised for errors returned by Fragment's API responses."""


class NetworkError(FragmentAPIError):
    """Fragment could not be reached (timeout, refused or dropped connection). Nothing was sent."""

    retryable = True

    UNREACHABLE = "Could not reach Fragment at {url}: {exc}"


class ServerError(FragmentAPIError):
    """Fragment answered "Server error" in the body of an HTTP 200, which it does now and then. Repeat the call."""

    retryable = True


class HTTPStatusError(FragmentAPIError):
    """Fragment answered with an unexpected HTTP status."""

    UNAVAILABLE = "Fragment is temporarily unavailable: HTTP {status} from {url}. Retry in a moment."
    BAD_STATUS = "Fragment returned HTTP {status} for {url}."

    def __init__(self, status: int, url: str) -> None:
        self.status = status
        self.url = url
        transient = status == HTTPStatus.TOO_MANY_REQUESTS or status >= HTTPStatus.INTERNAL_SERVER_ERROR
        template = self.UNAVAILABLE if transient else self.BAD_STATUS
        super().__init__(template.format(status=status, url=url), retryable=transient)

    def __reduce__(self) -> tuple[type, tuple[int, str]]:
        return (self.__class__, (self.status, self.url))


class SessionExpiredError(FragmentAPIError):
    """The Fragment session behind the cookies is no longer logged in: refresh the cookies."""

    REJECTED = "Fragment rejected the session (HTTP {status} from {url}). Log in to fragment.com and refresh your cookies."
    ACCESS_DENIED = (
        "Fragment denied access to '{context}'. "
        "Either your session has expired (refresh stel_token) "
        "or your TON wallet is not connected on Fragment (refresh stel_ton_token)."
    )
    NEED_TON = (
        "Fragment says no TON wallet is connected to this session (need_ton) for '{context}'. "
        "Connect the wallet on fragment.com and refresh stel_ton_token."
    )
    NO_REQUEST_ID = (
        "Fragment did not return a request ID for '{context}'. Your session has likely expired: refresh your cookies."
    )
    NO_HASH = (
        "Could not find the API hash on {url}: you are not logged in, or Fragment changed its page layout. "
        "Refresh your cookies; if that doesn't help, update pyfragment."
    )
    NOT_LOGGED_IN = (
        "Fragment returned a logged-out page for {url}. "
        "Refresh your stel_token / stel_ton_token cookies and log in to fragment.com again."
    )
    STALE_HASH = (
        "Fragment rejected a freshly fetched API hash from {url}: your session may have expired. "
        "Refresh your cookies; if that doesn't help, update pyfragment."
    )


class RecipientError(FragmentAPIError):
    """The recipient of a purchase can't receive it."""


class UserNotFoundError(RecipientError):
    """Raised when the target Telegram user is not found on Fragment."""

    NOT_FOUND = (
        "Telegram user '{username}' was not found on Fragment. Double-check the username and make sure the account exists."
    )
    NOT_A_USER = (
        "'{username}' does not belong to a user account: it either doesn't exist or is a channel or bot. "
        "Make sure the username is assigned to a personal Telegram account."
    )


class ChannelNotFoundError(RecipientError):
    """Raised when the target Telegram channel is not found on Fragment."""

    NOT_FOUND = (
        "Telegram channel '{channel}' was not found on Fragment. Double-check the channel username and make sure it exists."
    )
    NOT_A_CHANNEL = (
        "'{channel}' does not belong to a channel: it is a user, a bot or doesn't exist. "
        "Make sure the username is assigned to a Telegram channel."
    )


class AlreadySubscribedError(RecipientError):
    """Raised when trying to gift Premium to a user who already has an active subscription."""

    PREMIUM_ACTIVE = "This account is already subscribed to Telegram Premium."


class AmountError(FragmentAPIError):
    """Fragment refuses an amount, or a count, that is out of the bounds it sells at (they can depend on the recipient)."""

    minimum: int | None = None
    """The smallest amount Fragment accepts, when its message states one."""
    maximum: int | None = None
    """The largest amount Fragment accepts, when its message states one."""

    def __init__(self, message: str, minimum: int | None = None, maximum: int | None = None) -> None:
        super().__init__(message)
        self.minimum = minimum
        self.maximum = maximum

    @classmethod
    def from_text(cls, text: str) -> AmountError:
        """Fragment's "from A to B" message, which names both bounds."""
        bounds = numbers_in(text)[:2]
        return cls(text, *bounds) if len(bounds) == 2 else cls(text)


class BelowMinimumError(AmountError):
    """The amount is under the minimum Fragment sells (e.g. "You can buy a minimum of 35,000 stars")."""

    @classmethod
    def from_text(cls, text: str) -> BelowMinimumError:
        return cls(text, minimum=next(iter(numbers_in(text)), None))


class AboveMaximumError(AmountError):
    """The amount is over the maximum Fragment sells (e.g. "You can choose up to 5 winners for the selected package")."""

    @classmethod
    def from_text(cls, text: str) -> AboveMaximumError:
        return cls(text, maximum=next(iter(numbers_in(text)), None))


class InvalidPackageError(FragmentAPIError):
    """Fragment only sells fixed packages and the one asked for is not among them."""


class InvoiceExpiredError(FragmentAPIError):
    """Fragment no longer knows the invoice (it expired before the transaction was requested). Nothing was paid."""

    retryable = True

    EXPIRED = "Fragment no longer has the invoice for '{context}': it expired before it was paid. Start the purchase again."


class WalletAlreadyLinkedError(FragmentAPIError):
    """The wallet is already linked to a Fragment account."""

    LINKED = "This wallet is already linked to a Fragment account."


class AnonymousNumberError(FragmentAPIError):
    """Raised for Fragment anonymous number API failures."""

    NOT_OWNED = "Number '{number}' is not associated with your Fragment account or has no active sessions to terminate."
    TERMINATE_FAILED = "Failed to terminate sessions for '{number}': {error}"
    TOGGLE_FAILED = "Failed to toggle login codes for '{number}': {error}"


class ParseError(FragmentAPIError):
    """Raised when a Fragment API response or payload cannot be parsed."""

    UNPARSEABLE = "Failed to parse the Fragment API response for '{context}': {exc}"


class VerificationError(FragmentAPIError):
    """Raised when Fragment requires verification before proceeding."""

    KYC_REQUIRED = (
        "Fragment requires verification before this action can be completed. "
        f"Check {PROFILE_PAGE}: either identity verification (KYC) is pending, "
        "or the wallet used here is not linked to your Fragment account "
        "(the connected wallet address must match the one the library signs with)."
    )


class ChainError(FragmentError):
    """Raised for failures on the GRAM (ex TON) side: the wallet, its balance, the blockchain API provider."""


class ProviderError(ChainError):
    """The blockchain API provider (tonapi or toncenter) failed or is unreachable. Nothing was sent."""

    BALANCE_CHECK_FAILED = "Failed to fetch the {currency} balance: {exc}"
    WALLET_STATE_FAILED = "Failed to fetch the wallet state: {exc}"
    WALLET_INFO_FAILED = "Failed to retrieve wallet info from the GRAM (ex TON) network: {exc}"

    @classmethod
    def from_exception(cls, template: str, exc: BaseException, **fields: object) -> ProviderError:
        """The error for a failed provider call, carrying the HTTP status when the provider answered with one."""
        status = exc.code if isinstance(exc, ProviderResponseError) else None
        return cls(template.format(exc=exc, **fields), status)

    def __init__(self, message: str, status: int | None = None) -> None:
        self.status = status
        transient = status is None or status == HTTPStatus.TOO_MANY_REQUESTS or status >= HTTPStatus.INTERNAL_SERVER_ERROR
        super().__init__(message, retryable=transient)


class TransactionError(ChainError):
    """Fragment's transaction can't be signed. Nothing was sent."""

    INVALID_PAYLOAD = "Fragment returned an invalid transaction payload: 'transaction.messages' is missing or empty."
    MULTIPLE_MESSAGES = "Fragment asked for a transaction of {count} messages; pyfragment only signs single-message transfers."
    EXPIRED = "Fragment's transaction expired at {valid_until} (unix time) before it could be signed."

    @classmethod
    def expired(cls, valid_until: int) -> TransactionError:
        return cls(cls.EXPIRED.format(valid_until=valid_until), retryable=True)


class UnexpectedError(FragmentError):
    """Raised when an unexpected error occurs during an API call. Nothing was sent."""

    UNEXPECTED = "An unexpected error occurred during the operation: {exc}"


__all__ = [
    "FragmentError",
    "ClientError",
    "ConfigurationError",
    "CookieError",
    "FragmentAPIError",
    "NetworkError",
    "HTTPStatusError",
    "ServerError",
    "SessionExpiredError",
    "RecipientError",
    "UserNotFoundError",
    "ChannelNotFoundError",
    "AlreadySubscribedError",
    "AmountError",
    "BelowMinimumError",
    "AboveMaximumError",
    "InvalidPackageError",
    "InvoiceExpiredError",
    "WalletAlreadyLinkedError",
    "AnonymousNumberError",
    "ParseError",
    "VerificationError",
    "ChainError",
    "ProviderError",
    "TransactionError",
    "UnexpectedError",
]
