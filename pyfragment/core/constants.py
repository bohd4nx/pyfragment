from __future__ import annotations

from typing import Any

FRAGMENT_DOMAIN: str = "fragment.com"
FRAGMENT_BASE_URL: str = f"https://{FRAGMENT_DOMAIN}"
FRAGMENT_API_URL: str = f"{FRAGMENT_BASE_URL}/api"

STARS_PAGE: str = f"{FRAGMENT_BASE_URL}/stars/buy"
STARS_GIVEAWAY_PAGE: str = f"{FRAGMENT_BASE_URL}/stars/giveaway"
PREMIUM_PAGE: str = f"{FRAGMENT_BASE_URL}/premium/gift"
PREMIUM_GIVEAWAY_PAGE: str = f"{FRAGMENT_BASE_URL}/premium/giveaway"
ADS_TOPUP_PAGE: str = f"{FRAGMENT_BASE_URL}/ads/topup"
NUMBERS_PAGE: str = f"{FRAGMENT_BASE_URL}/numbers"
GIFTS_PAGE: str = f"{FRAGMENT_BASE_URL}/gifts"

DEFAULT_TIMEOUT: float = 30.0

# Attempts (initial try included) for Fragment API calls that hit HTTP 429, and for wallet broadcasts
MAX_API_ATTEMPTS: int = 3
MAX_BROADCAST_ATTEMPTS: int = 3

# How long (and how often) to poll Fragment for its own on-chain purchase confirmation
CONFIRM_STATE_TIMEOUT: float = 60.0
CONFIRM_STATE_POLL_INTERVAL: float = 2.0

# Fragment cookie keys required for authenticated API calls
REQUIRED_COOKIE_KEYS: tuple[str, ...] = ("stel_ssid", "stel_dt", "stel_token", "stel_ton_token")

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
NANO_PER_GRAM: int = 1_000_000_000
USDT_UNITS: int = 1_000_000

# TON Connect network id of the mainnet, as sent in the wallet account payload
MAINNET_CHAIN_ID: str = "-239"

# USDT-TON jetton master contract address on GRAM (ex TON) mainnet
USDT_GRAM_MASTER_ADDRESS: str = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"

# TON Connect device info sent during wallet connection handshake
DEVICE_INFO: dict[str, Any] = {
    "platform": "iphone",
    "appName": "Tonkeeper",
    "appVersion": "26.07.1",
    "maxProtocolVersion": 2,
    "features": [
        "SendTransaction",
        {"name": "SendTransaction", "maxMessages": 255},
        {"name": "SignData", "types": ["text", "binary", "cell"]},
    ],
}

# Stars: direct purchase per transaction
STARS_PURCHASE_MIN: int = 50
STARS_PURCHASE_MAX: int = 10_000_000

# Stars: giveaway amount per winner
STARS_GIVEAWAY_MIN: int = 500
STARS_GIVEAWAY_MAX: int = 1_000_000

# Stars giveaway winner count
STARS_WINNERS_MIN: int = 1
STARS_WINNERS_MAX: int = 5

# Premium giveaway winner count
PREMIUM_WINNERS_MIN: int = 1
PREMIUM_WINNERS_MAX: int = 24_000

# GRAM (ex TON) topup / Ads recharge amount
GRAM_TOPUP_MIN: int = 1
GRAM_TOPUP_MAX: int = 1_000_000_000

# Minimum wallet balances required before broadcasting a transaction
MIN_GRAM_BALANCE: float = 0.33
MIN_USDT_BALANCE: float = 0.75

# Premium subscription durations (months)
PREMIUM_MONTHS_VALID: frozenset[int] = frozenset({3, 6, 12})

# Mnemonic phrase valid word counts
MNEMONIC_WORD_COUNTS_VALID: frozenset[int] = frozenset({12, 24})
