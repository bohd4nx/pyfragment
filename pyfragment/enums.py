from __future__ import annotations

from enum import StrEnum


class PaymentMethod(StrEnum):
    """How a purchase is paid. Fragment also offers non-TON chains, which this library can't sign for."""

    GRAM = "ton"
    USDT_GRAM = "usdt_ton"


class WalletVersion(StrEnum):
    V4R2 = "V4R2"
    V5R1 = "V5R1"
    HighloadV2 = "HighloadV2"
    HighloadV3R1 = "HighloadV3R1"
    TG = "TG"  # Telegram Wallet (self-custodial): a 12-word phrase, or 24 words after a key rotation


class MnemonicType(StrEnum):
    """How a seed phrase derives the wallet key."""

    TON = "ton"  # TON's own scheme: Tonkeeper, MyTonWallet, Tonhub and other TON-only wallets
    MULTICHAIN = "multichain"  # BIP-39 phrase, key at m/44'/607'/0': Telegram Wallet and multichain wallets


class ApiProvider(StrEnum):
    """Blockchain API provider used to read the wallet and broadcast transactions."""

    TONAPI = "tonapi"  # tonconsole.com — get a key at tonconsole.com (default)
    TONCENTER = "toncenter"  # t.me/toncenter — get a key via @tonapibot


class ApiMethod(StrEnum):
    """Method names of Fragment's ``/api`` endpoint used by this library.

    ``FragmentClient.call()`` also accepts any other method name as a plain string.
    """

    # Stars purchase
    SEARCH_STARS_RECIPIENT = "searchStarsRecipient"
    UPDATE_STARS_BUY_STATE = "updateStarsBuyState"
    INIT_BUY_STARS_REQUEST = "initBuyStarsRequest"
    GET_BUY_STARS_LINK = "getBuyStarsLink"

    # Premium gift
    SEARCH_PREMIUM_GIFT_RECIPIENT = "searchPremiumGiftRecipient"
    UPDATE_PREMIUM_STATE = "updatePremiumState"
    INIT_GIFT_PREMIUM_REQUEST = "initGiftPremiumRequest"
    GET_GIFT_PREMIUM_LINK = "getGiftPremiumLink"

    # Stars giveaway
    SEARCH_STARS_GIVEAWAY_RECIPIENT = "searchStarsGiveawayRecipient"
    UPDATE_STARS_GIVEAWAY_STATE = "updateStarsGiveawayState"
    UPDATE_STARS_GIVEAWAY_PRICES = "updateStarsGiveawayPrices"
    INIT_GIVEAWAY_STARS_REQUEST = "initGiveawayStarsRequest"
    GET_GIVEAWAY_STARS_LINK = "getGiveawayStarsLink"

    # Premium giveaway
    SEARCH_PREMIUM_GIVEAWAY_RECIPIENT = "searchPremiumGiveawayRecipient"
    UPDATE_PREMIUM_GIVEAWAY_STATE = "updatePremiumGiveawayState"
    UPDATE_PREMIUM_GIVEAWAY_PRICES = "updatePremiumGiveawayPrices"
    INIT_GIVEAWAY_PREMIUM_REQUEST = "initGiveawayPremiumRequest"
    GET_GIVEAWAY_PREMIUM_LINK = "getGiveawayPremiumLink"

    # GRAM (ex TON) topup for a Telegram user
    UPDATE_ADS_TOPUP_STATE = "updateAdsTopupState"
    SEARCH_ADS_TOPUP_RECIPIENT = "searchAdsTopupRecipient"
    INIT_ADS_TOPUP_REQUEST = "initAdsTopupRequest"
    GET_ADS_TOPUP_LINK = "getAdsTopupLink"

    # Ads account recharge
    UPDATE_ADS_STATE = "updateAdsState"
    INIT_ADS_RECHARGE_REQUEST = "initAdsRechargeRequest"
    GET_ADS_RECHARGE_LINK = "getAdsRechargeLink"

    # Marketplace
    SEARCH_AUCTIONS = "searchAuctions"

    # Anonymous numbers
    UPDATE_LOGIN_CODES = "updateLoginCodes"
    TOGGLE_LOGIN_CODES = "toggleLoginCodes"
    TERMINATE_PHONE_SESSIONS = "terminatePhoneSessions"


class ApiError(StrEnum):
    """Error messages Fragment returns in the ``error`` field of an HTTP 200 response.

    Fragment reports API failures in the body, not in the HTTP status. Members are matched as
    case-insensitive substrings of the response's error text.
    """

    BAD_REQUEST = "Bad request"  # unknown or stale `hash` query parameter, or a malformed request
    INVALID_METHOD = "Invalid method"
    ACCESS_DENIED = "Access denied"
    NOT_A_USER = "assigned to a user"  # "Please enter a username assigned to a user."
    NO_USERS_FOUND = "No Telegram users found"
    NO_CHANNELS_FOUND = "No Telegram channels found"
    ALREADY_SUBSCRIBED = "already subscribed to telegram premium"


class StateMode(StrEnum):
    """``mode`` of a Fragment purchase page state; it moves new -> processing -> done."""

    NEW = "new"
    PROCESSING = "processing"
    DONE = "done"


class MarketplaceType(StrEnum):
    """``type`` of a ``searchAuctions`` request."""

    USERNAMES = "usernames"
    NUMBERS = "numbers"
    GIFTS = "gifts"


class AuctionSort(StrEnum):
    """Sort orders of the Fragment marketplace. Fragment silently ignores unknown values."""

    PRICE = "price"  # the marketplace default
    PRICE_DESC = "price_desc"
    PRICE_ASC = "price_asc"
    LISTED = "listed"
    ENDING = "ending"


class AuctionFilter(StrEnum):
    """Listing filters of the Fragment marketplace. Fragment silently ignores unknown values."""

    AVAILABLE = ""  # the marketplace default
    AUCTION = "auction"
    SALE = "sale"
    SOLD = "sold"


class GiftAttribute(StrEnum):
    """Traits a collection of gifts can be filtered by. Fragment silently ignores unknown (or differently cased) names."""

    MODEL = "Model"
    BACKDROP = "Backdrop"
    SYMBOL = "Symbol"
