# Copyright (c) 2026 bohd4nx
#
# This source code is licensed under the MIT License found in the
# LICENSE file in the root directory of this source tree.

from importlib.metadata import version

from pyfragment.client import FragmentClient
from pyfragment.types import (
    AdsRechargeResult,
    AdsTopupResult,
    AnonymousNumberError,
    ClientError,
    ConfigurationError,
    CookieError,
    FragmentAPIError,
    FragmentError,
    FragmentPageError,
    GiftsResult,
    LoginCodeResult,
    NumbersResult,
    OperationError,
    ParseError,
    PremiumGiveawayResult,
    PremiumResult,
    StarsGiveawayResult,
    StarsResult,
    TerminateSessionsResult,
    TransactionError,
    UnexpectedError,
    UsernamesResult,
    UserNotFoundError,
    VerificationError,
    WalletError,
    WalletInfo,
)
from pyfragment.utils.cookies import get_cookies_from_browser

__version__: str = version("pyfragment")

__all__ = [
    "__version__",
    "FragmentClient",
    "get_cookies_from_browser",
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
    "ClientError",
    "ConfigurationError",
    "CookieError",
    "FragmentAPIError",
    "FragmentError",
    "FragmentPageError",
    "AnonymousNumberError",
    "OperationError",
    "ParseError",
    "TransactionError",
    "UnexpectedError",
    "UserNotFoundError",
    "VerificationError",
    "WalletError",
]
