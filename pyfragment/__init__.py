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
    CookieResult,
    FragmentAPIError,
    # exceptions
    FragmentError,
    FragmentPageError,
    GiftsResult,
    LoginCodeResult,
    NumbersResult,
    OperationError,
    ParseError,
    # literal types
    PaymentMethod,
    PremiumGiveawayResult,
    PremiumResult,
    StarsGiveawayResult,
    # results
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
]
