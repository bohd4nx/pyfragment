"""Exceptions raised by pyfragment.

``retryable`` means nothing was paid and repeating the call may succeed. Only a ``BroadcastError`` with
``retryable=False`` leaves the payment's outcome unknown.
"""

from __future__ import annotations

from decimal import Decimal
from http import HTTPStatus
from typing import TYPE_CHECKING

from pyfragment.constants import (
    GRAM_TOPUP_MAX,
    GRAM_TOPUP_MIN,
    PREMIUM_MONTHS_VALID,
    PREMIUM_WINNERS_MAX,
    PREMIUM_WINNERS_MIN,
    STARS_GIVEAWAY_MAX,
    STARS_GIVEAWAY_MIN,
    STARS_PURCHASE_MAX,
    STARS_PURCHASE_MIN,
    STARS_WINNERS_MAX,
    STARS_WINNERS_MIN,
)

if TYPE_CHECKING:
    from pyfragment.domains.wallet.models import TransferIntent


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
    UNSUPPORTED_VERSION = "Unsupported wallet version '{version}'. Supported values: {supported}."
    UNSUPPORTED_MNEMONIC_TYPE = "Unsupported mnemonic type '{mnemonic_type}'. Supported values: {supported}."
    INVALID_SEED = "Invalid seed phrase: {exc}"
    INVALID_GAS_RESERVE = "Invalid gas_reserve '{value}': must be a non-negative amount of GRAM (ex TON)."
    INVALID_CONFIRM_TIMEOUT = "Invalid confirm_timeout '{value}': must be a non-negative number of seconds."
    UNSUPPORTED_PROVIDER = "Unsupported API provider '{provider}'. Supported values: {supported}."
    INVALID_MONTHS = f"Invalid Premium duration: choose {', '.join(str(m) for m in sorted(PREMIUM_MONTHS_VALID))} months."
    INVALID_STARS_AMOUNT = (
        f"Invalid Stars amount: must be an integer between {STARS_PURCHASE_MIN:,} and {STARS_PURCHASE_MAX:,}."
    )
    INVALID_GRAM_AMOUNT = f"Invalid GRAM (ex TON) amount: must be an integer between {GRAM_TOPUP_MIN:,} and {GRAM_TOPUP_MAX:,}."
    INVALID_WINNERS_STARS = (
        f"Invalid winners count: must be an integer between {STARS_WINNERS_MIN:,} and {STARS_WINNERS_MAX:,}."
    )
    INVALID_WINNERS_PREMIUM = (
        f"Invalid winners count: must be an integer between {PREMIUM_WINNERS_MIN:,} and {PREMIUM_WINNERS_MAX:,}."
    )
    INVALID_STARS_PER_WINNER = (
        f"Invalid Stars per winner: must be an integer between {STARS_GIVEAWAY_MIN:,} and {STARS_GIVEAWAY_MAX:,}."
    )
    INVALID_SORT = "Invalid sort order '{sort}'. Supported values: {supported}."
    INVALID_FILTER = "Invalid filter '{filter}'. Supported values: {supported}."
    INVALID_GIFT_ATTRIBUTE = "Invalid gift attribute '{attribute}'. Supported values: {supported}."
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


class SessionExpiredError(FragmentAPIError):
    """The Fragment session behind the cookies is no longer logged in: refresh the cookies."""

    REJECTED = "Fragment rejected the session (HTTP {status} from {url}). Log in to fragment.com and refresh your cookies."
    ACCESS_DENIED = "Fragment denied access to '{context}'. Your session has likely expired: refresh your cookies."
    NO_REQUEST_ID = (
        "Fragment did not return a request ID for '{context}'. Your session has likely expired: refresh your cookies."
    )
    NO_HASH = (
        "Could not find the API hash on {url}: you are not logged in, or Fragment changed its page layout. "
        "Refresh your cookies; if that doesn't help, update pyfragment."
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


class AlreadySubscribedError(RecipientError):
    """Raised when trying to gift Premium to a user who already has an active subscription."""

    PREMIUM_ACTIVE = "This account is already subscribed to Telegram Premium."


class AnonymousNumberError(FragmentAPIError):
    """Raised for Fragment anonymous number API failures."""

    NOT_OWNED = "Number '{number}' is not associated with your Fragment account or has no active sessions to terminate."
    TERMINATE_FAILED = "Failed to terminate sessions for '{number}': {error}"
    TOGGLE_FAILED = "Failed to toggle login codes for '{number}': {error}"


class ParseError(FragmentAPIError):
    """Raised when a Fragment API response or payload cannot be parsed."""

    UNPARSEABLE = "Failed to parse the Fragment API response for '{context}': {exc}"


class VerificationError(FragmentAPIError):
    """Raised when Fragment requires KYC verification before proceeding."""

    KYC_REQUIRED = (
        "Fragment requires identity verification (KYC) before this action can be completed. "
        "Complete verification at https://fragment.com/my/profile and retry."
    )


class ChainError(FragmentError):
    """Raised for failures on the GRAM (ex TON) side: the wallet, its balance, the blockchain API provider."""


class InsufficientBalanceError(ChainError):
    """The wallet can't cover the payment plus the gas reserve. Nothing was sent."""

    LOW_BALANCE = "Insufficient {currency} balance: {balance} {currency} available, {required} {currency} required."

    def __init__(self, balance: Decimal, required: Decimal, currency: str) -> None:
        self.balance = balance
        self.required = required
        self.currency = currency
        super().__init__(
            self.LOW_BALANCE.format(balance=format(balance, "f"), required=format(required, "f"), currency=currency)
        )


class ProviderError(ChainError):
    """The blockchain API provider (tonapi or toncenter) failed or is unreachable. Nothing was sent."""

    BALANCE_CHECK_FAILED = "Failed to fetch the {currency} balance: {exc}"
    WALLET_STATE_FAILED = "Failed to fetch the wallet state: {exc}"
    WALLET_INFO_FAILED = "Failed to retrieve wallet info from the GRAM (ex TON) network: {exc}"
    TRANSFER_LOOKUP_FAILED = "Failed to look the transfer up on the GRAM (ex TON) network: {exc}"

    def __init__(self, message: str, status: int | None = None) -> None:
        self.status = status
        super().__init__(message, retryable=True)


class TransactionError(ChainError):
    """Fragment's transaction can't be signed. Nothing was sent."""

    INVALID_PAYLOAD = "Fragment returned an invalid transaction payload: 'transaction.messages' is missing or empty."
    MULTIPLE_MESSAGES = "Fragment asked for a transaction of {count} messages; pyfragment only signs single-message transfers."
    EXPIRED = "Fragment's transaction expired at {valid_until} (unix time) before it could be signed."


class BroadcastError(ChainError):
    """The signed transfer didn't go through, or its outcome couldn't be checked.

    ``retryable`` is ``True`` when the transfer certainly didn't pay anything. When it is ``False`` the outcome is
    unknown: check ``transfer.msg_hash`` in your wallet's transaction history before paying again.
    """

    NOT_SENT = "Transaction {msg_hash} was not sent: {exc}. Nothing was paid."
    NOT_LANDED = "Transaction {msg_hash} did not reach the chain before it expired. Nothing was paid."
    FAILED = "Transaction {msg_hash} reached the chain, but the wallet didn't pay (not enough funds?). Nothing was paid."
    UNKNOWN = (
        "Transaction {msg_hash} was sent, but whether it paid couldn't be checked: {exc}. "
        "Check your wallet's transaction history by msg_hash before paying again."
    )
    SSL_HINT = (
        "\nThis usually means your system's CA bundle is missing or outdated. Fix: run `pip install --upgrade certifi`; "
        "on macOS you may also need to run the 'Install Certificates.command' located in your Python installation folder."
    )

    def __init__(self, message: str, transfer: TransferIntent, retryable: bool) -> None:
        self.transfer = transfer
        super().__init__(message, retryable=retryable)


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
    "SessionExpiredError",
    "RecipientError",
    "UserNotFoundError",
    "ChannelNotFoundError",
    "AlreadySubscribedError",
    "AnonymousNumberError",
    "ParseError",
    "VerificationError",
    "ChainError",
    "InsufficientBalanceError",
    "ProviderError",
    "TransactionError",
    "BroadcastError",
    "UnexpectedError",
]
