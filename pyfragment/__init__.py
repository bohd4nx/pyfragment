import logging
from importlib.metadata import version

from pyfragment.client import FragmentClient
from pyfragment.domains.ads.models import AdsRechargeResult, AdsTopupResult
from pyfragment.domains.anonymous_numbers.models import LoginCodeResult, TerminateSessionsResult
from pyfragment.domains.assets.models import MyGiftsResult, MyNumbersResult, MyUsernamesResult
from pyfragment.domains.giveaways.models import PremiumGiveawayResult, StarsGiveawayResult
from pyfragment.domains.marketplace.models import AuctionItem, GiftsResult, NumbersResult, UsernamesResult
from pyfragment.domains.payments.models import PaymentResult
from pyfragment.domains.purchases.models import PremiumPackage, PremiumResult, StarsPackage, StarsResult
from pyfragment.domains.recipients import Recipient
from pyfragment.domains.wallet.models import TransferIntent, WalletInfo
from pyfragment.enums import (
    ApiError,
    ApiMethod,
    ApiProvider,
    AuctionFilter,
    AuctionSort,
    GiftAttribute,
    MarketplaceType,
    MnemonicType,
    PaymentMethod,
    StateMode,
    WalletVersion,
)
from pyfragment.exceptions import (
    AlreadySubscribedError,
    AnonymousNumberError,
    ChainError,
    ChannelNotFoundError,
    ClientError,
    ConfigurationError,
    CookieError,
    FragmentAPIError,
    FragmentError,
    HTTPStatusError,
    InsufficientBalanceError,
    NetworkError,
    ParseError,
    ProviderError,
    RecipientError,
    SessionExpiredError,
    TransactionError,
    UnexpectedError,
    UserNotFoundError,
    VerificationError,
)

logging.getLogger("pyfragment").addHandler(logging.NullHandler())

__version__: str = version("pyfragment")

__all__ = [
    "__version__",
    "FragmentClient",
    # results
    "PaymentResult",
    "StarsPackage",
    "StarsResult",
    "StarsGiveawayResult",
    "PremiumPackage",
    "PremiumResult",
    "PremiumGiveawayResult",
    "WalletInfo",
    "TransferIntent",
    "Recipient",
    "AdsTopupResult",
    "AdsRechargeResult",
    "AuctionItem",
    "GiftsResult",
    "LoginCodeResult",
    "MyGiftsResult",
    "MyNumbersResult",
    "MyUsernamesResult",
    "NumbersResult",
    "TerminateSessionsResult",
    "UsernamesResult",
    # exceptions
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
    "VerificationError",
    "ParseError",
    "AnonymousNumberError",
    "ChainError",
    "InsufficientBalanceError",
    "ProviderError",
    "TransactionError",
    "UnexpectedError",
    # enums
    "ApiError",
    "ApiMethod",
    "ApiProvider",
    "AuctionFilter",
    "AuctionSort",
    "GiftAttribute",
    "MarketplaceType",
    "MnemonicType",
    "PaymentMethod",
    "StateMode",
    "WalletVersion",
]
