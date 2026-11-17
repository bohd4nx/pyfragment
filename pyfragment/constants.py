from __future__ import annotations

from typing import Any, NamedTuple

from pyfragment.enums import Limit


class Range(NamedTuple):
    label: str
    min: int
    max: int


FRAGMENT_BASE_URL: str = "https://fragment.com"
FRAGMENT_API_URL: str = f"{FRAGMENT_BASE_URL}/api"

STARS_PAGE: str = f"{FRAGMENT_BASE_URL}/stars/buy"
STARS_GIVEAWAY_PAGE: str = f"{FRAGMENT_BASE_URL}/stars/giveaway"
PREMIUM_PAGE: str = f"{FRAGMENT_BASE_URL}/premium/gift"
PREMIUM_GIVEAWAY_PAGE: str = f"{FRAGMENT_BASE_URL}/premium/giveaway"
ADS_TOPUP_PAGE: str = f"{FRAGMENT_BASE_URL}/ads/topup"
PROFILE_PAGE: str = f"{FRAGMENT_BASE_URL}/my/profile"
MY_USERNAMES_PAGE: str = f"{FRAGMENT_BASE_URL}/my/usernames"
MY_NUMBERS_PAGE: str = f"{FRAGMENT_BASE_URL}/my/numbers"
MY_GIFTS_PAGE: str = f"{FRAGMENT_BASE_URL}/my/gifts"
NUMBERS_PAGE: str = f"{FRAGMENT_BASE_URL}/numbers"
GIFTS_PAGE: str = f"{FRAGMENT_BASE_URL}/gifts"

DEFAULT_TIMEOUT: float = 30.0

# Attempts (initial try included) for a Fragment API call that hits HTTP 429
MAX_API_ATTEMPTS: int = 3

# Default for how long to poll Fragment for its own on-chain purchase confirmation, and how often
CONFIRM_STATE_TIMEOUT: float = 60.0
CONFIRM_STATE_POLL_INTERVAL: float = 2.0

# How long a signed transfer stays valid: after that the wallet rejects it, so it can never land late
MESSAGE_TTL: int = 60
# How often a transfer looks for the previous one to land before taking the next seqno (about a quarter of a block)
SEQNO_POLL_INTERVAL: float = 1.0
# Transfers sent in one external message unless FragmentClient(max_batch=...) says otherwise
DEFAULT_MAX_BATCH: int = 1
# Fragment cookie keys required for authenticated API calls
REQUIRED_COOKIE_KEYS: tuple[str, ...] = ("stel_ssid", "stel_dt", "stel_token")

# Headers for Fragment's JSON API calls (POST /api?hash=...). curl_cffi's impersonate="chrome"
# already supplies a browser-consistent User-Agent, Sec-Ch-Ua*, Accept-Language, and
# Accept-Encoding tied to its actual TLS/HTTP2 fingerprint — hardcoding those here would only
# risk them drifting out of sync with what curl_cffi is really sending on the wire. What's left
# is only what genuinely differs for an XHR-style call vs. curl_cffi's page-navigation defaults,
# plus two navigation-only fields curl_cffi sets by default that a real XHR call never sends.
BASE_HEADERS: dict[str, str | None] = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": FRAGMENT_BASE_URL,
    "priority": "u=1, i",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": None,
    "upgrade-insecure-requests": None,
    "x-requested-with": "XMLHttpRequest",
}

# Smallest units: 1 GRAM (ex TON) = 10^9 nanograms, 1 USDT = 10^6 units
GRAM_DECIMALS: int = 9
USDT_DECIMALS: int = 6
USDT_CURRENCY: str = "USDT"

# TVM exit code of a get-method called on a contract that isn't deployed (toncenter reports it as an error)
TVM_EXIT_ACCOUNT_NOT_FOUND: int = -13

# TON Connect network id of the mainnet, as sent in the wallet account payload
MAINNET_CHAIN_ID: str = "-239"

# USDT-TON jetton master contract address on GRAM (ex TON) mainnet
USDT_GRAM_MASTER_ADDRESS: str = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"

# TON Connect device info sent during wallet connection handshake.
# Based on wallets-v2.json from config.ton.org/wallets-v2.json — updated 2026-10.
DEVICE_INFO: dict[str, Any] = {
    "platform": "iphone",
    "appName": "Tonkeeper",
    "appVersion": "26.10.1",
    "maxProtocolVersion": 2,
    "features": [
        {"name": "SendTransaction", "maxMessages": 255, "extraCurrencySupported": True},
        {"name": "SignData", "types": ["text", "binary", "cell"]},
    ],
}

# Inclusive bounds of the amounts and counts Fragment accepts
LIMITS: dict[Limit, Range] = {
    Limit.STARS_PURCHASE: Range("Stars amount", 50, 10_000_000),
    Limit.STARS_GIVEAWAY: Range("Stars per winner", 500, 1_000_000),
    Limit.STARS_WINNERS: Range("winners count", 1, 5),
    Limit.PREMIUM_WINNERS: Range("winners count", 1, 24_000),
    Limit.GRAM_TOPUP: Range("GRAM (ex TON) amount", 1, 1_000_000_000),
}

# Premium subscription durations (months)
PREMIUM_MONTHS_VALID: frozenset[int] = frozenset({3, 6, 12})
