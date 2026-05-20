from __future__ import annotations

import json
from typing import Any

from tonutils.contracts.wallet import WalletV4R2, WalletV5R1

WALLET_CLASSES: dict[str, Any] = {"V4R2": WalletV4R2, "V5R1": WalletV5R1}

MIN_TON_BALANCE: float = 0.33
USDT_TON_MASTER_ADDRESS: str = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"
MIN_USDT_BALANCE: float = 0.75

DEFAULT_TIMEOUT: float = 30.0

REQUIRED_COOKIE_KEYS: tuple[str, ...] = ("stel_ssid", "stel_dt", "stel_token", "stel_ton_token")

FRAGMENT_DOMAIN: str = "fragment.com"
FRAGMENT_BASE_URL: str = f"https://{FRAGMENT_DOMAIN}"
STARS_PAGE: str = f"{FRAGMENT_BASE_URL}/stars/buy"
STARS_GIVEAWAY_PAGE: str = f"{FRAGMENT_BASE_URL}/stars/giveaway"
PREMIUM_PAGE: str = f"{FRAGMENT_BASE_URL}/premium/gift"
PREMIUM_GIVEAWAY_PAGE: str = f"{FRAGMENT_BASE_URL}/premium/giveaway"
ADS_TOPUP_PAGE: str = f"{FRAGMENT_BASE_URL}/ads/topup"
NUMBERS_PAGE: str = f"{FRAGMENT_BASE_URL}/numbers"
GIFTS_PAGE: str = f"{FRAGMENT_BASE_URL}/gifts"

SUPPORTED_BROWSERS: frozenset[str] = frozenset(
    {
        "arc",
        "brave",
        "chrome",
        "chromium",
        "chromium_based",
        "edge",
        "firefox",
        "firefox_based",
        "librewolf",
        "opera",
        "opera_gx",
        "safari",
        "vivaldi",
    }
)

DEVICE: str = json.dumps(
    {
        "platform": "iphone",
        "appName": "Tonkeeper",
        "appVersion": "26.04.0",
        "maxProtocolVersion": 2,
        "features": [
            "SendTransaction",
            {"name": "SendTransaction", "maxMessages": 255},
            {"name": "SignData", "types": ["text", "binary", "cell"]},
        ],
    }
)

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
