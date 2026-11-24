import logging
from importlib.metadata import version

from pyfragment.client import FragmentClient
from pyfragment.domains.anonymous_numbers.models import LoginCodeResult, TerminateSessionsResult
from pyfragment.domains.assets.models import MyGiftsResult, MyNumbersResult, MyUsernamesResult
from pyfragment.domains.giveaways.models import PremiumGiveawayResult, StarsGiveawayResult
from pyfragment.domains.history import PremiumHistoryEntry, StarsHistoryEntry
from pyfragment.domains.marketplace.models import AuctionItem, GiftsResult, NumbersResult, UsernamesResult
from pyfragment.domains.payments.models import PaymentResult
from pyfragment.domains.purchases.models import PremiumPackage, PremiumResult, StarsPackage, StarsResult
from pyfragment.domains.recipients import Recipient
from pyfragment.domains.wallet.models import TransferIntent, WalletInfo
from pyfragment.domains.wallet.transfers import LocalTransferCoordinator, TransferCoordinator
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
    AboveMaximumError,
    AlreadySubscribedError,
    AmountError,
    AnonymousNumberError,
    BelowMinimumError,
    ChainError,
    ChannelNotFoundError,
    ClientError,
    ConfigurationError,
    CookieError,
    FragmentAPIError,
    FragmentError,
    HTTPStatusError,
    InvalidPackageError,
    InvoiceExpiredError,
    NetworkError,
    ParseError,
    ProviderError,
    RecipientError,
    SessionExpiredError,
    TransactionError,
    UnexpectedError,
    UserNotFoundError,
    VerificationError,
    WalletAlreadyLinkedError,
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
    "StarsHistoryEntry",
    "PremiumHistoryEntry",
    "WalletInfo",
    "TransferIntent",
    "TransferCoordinator",
    "LocalTransferCoordinator",
    "Recipient",
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
    "AmountError",
    "BelowMinimumError",
    "AboveMaximumError",
    "InvalidPackageError",
    "InvoiceExpiredError",
    "WalletAlreadyLinkedError",
    "VerificationError",
    "ParseError",
    "AnonymousNumberError",
    "ChainError",
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
