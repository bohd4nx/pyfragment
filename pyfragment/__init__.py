# Copyright (c) 2025 bohd4nx
#
# This source code is licensed under the MIT License found in the
# LICENSE file in the root directory of this source tree.

from importlib.metadata import version

from pyfragment.client import FragmentClient
from pyfragment.types import (
    AdsTopupResult,
    ClientError,
    ConfigurationError,
    CookieError,
    FragmentAPIError,
    FragmentError,
    FragmentPageError,
    OperationError,
    ParseError,
    PremiumResult,
    StarsResult,
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
    "AdsTopupResult",
    "PremiumResult",
    "StarsResult",
    "WalletInfo",
    "ClientError",
    "ConfigurationError",
    "CookieError",
    "FragmentAPIError",
    "FragmentError",
    "FragmentPageError",
    "OperationError",
    "ParseError",
    "TransactionError",
    "UnexpectedError",
    "UserNotFoundError",
    "VerificationError",
    "WalletError",
]
