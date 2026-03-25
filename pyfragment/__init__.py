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
    AuctionsResult,
    ClientError,
    ConfigurationError,
    CookieError,
    FragmentAPIError,
    FragmentError,
    FragmentPageError,
    LoginCodeResult,
    OperationError,
    ParseError,
    PremiumGiveawayResult,
    PremiumResult,
    StarsGiveawayResult,
    StarsResult,
    TerminateSessionsResult,
    TransactionError,
    UnexpectedError,
    UserNotFoundError,
    VerificationError,
    WalletError,
    WalletInfo,
)

__version__: str = version("pyfragment")

__all__ = [
    "__version__",
    "FragmentClient",
    "AdsRechargeResult",
    "AdsTopupResult",
    "AuctionsResult",
    "LoginCodeResult",
    "PremiumGiveawayResult",
    "PremiumResult",
    "StarsGiveawayResult",
    "StarsResult",
    "TerminateSessionsResult",
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
