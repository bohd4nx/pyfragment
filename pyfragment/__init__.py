import logging
from importlib.metadata import version

from pyfragment.client import FragmentClient
from pyfragment.core.cookies import get_cookies_from_browser
from pyfragment.exceptions import (
    AlreadySubscribedError,
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
from pyfragment.domains.anonymous_numbers.models import LoginCodeResult, TerminateSessionsResult
from pyfragment.core.models import CookieResult
from pyfragment.enums import PaymentMethod, WalletVersion
from pyfragment.domains.giveaways.models import PremiumGiveawayResult, StarsGiveawayResult
from pyfragment.domains.marketplace.models import GiftsResult, NumbersResult, UsernamesResult
from pyfragment.domains.ads.models import AdsRechargeResult, AdsTopupResult
from pyfragment.domains.purchases.models import PremiumResult, StarsResult
from pyfragment.domains.tonapi.models import WalletInfo

logging.getLogger("pyfragment").addHandler(logging.NullHandler())

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
    "AlreadySubscribedError",
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
    "WalletVersion",
    "get_cookies_from_browser",
]
