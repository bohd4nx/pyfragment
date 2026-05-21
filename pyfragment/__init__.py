from importlib.metadata import version

from pyfragment.client import FragmentClient
from pyfragment.core.cookies import get_cookies_from_browser
from pyfragment.exceptions import (
    AnonymousNumberError,
    ClientError,
    ConfigurationError,
    CookieError,
    FragmentAPIError,
    FragmentError,
    FragmentPageError,
    OperationError,
    ParseError,
    TransactionError,
    UnexpectedError,
    UserNotFoundError,
    VerificationError,
    WalletError,
)
from pyfragment.models.anonymous_numbers import LoginCodeResult, TerminateSessionsResult
from pyfragment.models.cookies import CookieResult
from pyfragment.models.enums import PaymentMethod
from pyfragment.models.giveaways import PremiumGiveawayResult, StarsGiveawayResult
from pyfragment.models.marketplace import GiftsResult, NumbersResult, UsernamesResult
from pyfragment.models.payments import AdsRechargeResult, AdsTopupResult, PremiumResult, StarsResult
from pyfragment.models.wallet import WalletInfo

__version__: str = version("pyfragment")

__all__ = [
    "__version__",
    "FragmentClient",
    # results
    "StarsResult",
    "StarsGiveawayResult",
    "PremiumResult",
    "PremiumGiveawayResult",
    "WalletInfo",
    "AdsTopupResult",
    "AdsRechargeResult",
    "CookieResult",
    "GiftsResult",
    "LoginCodeResult",
    "NumbersResult",
    "TerminateSessionsResult",
    "UsernamesResult",
    # exceptions
    "FragmentError",
    "FragmentAPIError",
    "FragmentPageError",
    "ConfigurationError",
    "UserNotFoundError",
    "WalletError",
    "VerificationError",
    "TransactionError",
    "AnonymousNumberError",
    "ClientError",
    "CookieError",
    "OperationError",
    "ParseError",
    "UnexpectedError",
    # literal types
    "PaymentMethod",
    "get_cookies_from_browser",
]
