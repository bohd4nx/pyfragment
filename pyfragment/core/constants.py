from __future__ import annotations

from typing import Any

FRAGMENT_DOMAIN: str = "fragment.com"
FRAGMENT_BASE_URL: str = f"https://{FRAGMENT_DOMAIN}"

STARS_PAGE: str = f"{FRAGMENT_BASE_URL}/stars/buy"
STARS_GIVEAWAY_PAGE: str = f"{FRAGMENT_BASE_URL}/stars/giveaway"
PREMIUM_PAGE: str = f"{FRAGMENT_BASE_URL}/premium/gift"
PREMIUM_GIVEAWAY_PAGE: str = f"{FRAGMENT_BASE_URL}/premium/giveaway"
ADS_TOPUP_PAGE: str = f"{FRAGMENT_BASE_URL}/ads/topup"
NUMBERS_PAGE: str = f"{FRAGMENT_BASE_URL}/numbers"
GIFTS_PAGE: str = f"{FRAGMENT_BASE_URL}/gifts"

DEFAULT_TIMEOUT: float = 30.0

# Fragment cookie keys required for authenticated API calls
REQUIRED_COOKIE_KEYS: tuple[str, ...] = ("stel_ssid", "stel_dt", "stel_token", "stel_ton_token")

BASE_HEADERS: dict[str, str] = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-language": "en-US,en;q=0.9,uk;q=0.8,ru;q=0.7",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": FRAGMENT_BASE_URL,
    "priority": "u=1, i",
    "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"Android"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": (
        "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36"
    ),
    "x-requested-with": "XMLHttpRequest",
}

# USDT-TON jetton master contract address on GRAM (ex TON) mainnet
USDT_GRAM_MASTER_ADDRESS: str = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"

# TON Connect device info sent during wallet connection handshake
DEVICE_INFO: dict[str, Any] = {
    "platform": "iphone",
    "appName": "Tonkeeper",
    "appVersion": "26.05.0",
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
STARS_WINNERS_MAX: int = 15

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

# Tonapi API key minimum length (tonapi.io)
TONAPI_KEY_MIN_LENGTH: int = 68
