import json
from typing import Any, Literal, get_args

from tonutils.contracts.wallet import WalletV4R2, WalletV5R1

# Single source of truth for supported wallet versions
WalletVersion = Literal["V4R2", "V5R1"]
SUPPORTED_WALLET_VERSIONS: frozenset[str] = frozenset(get_args(WalletVersion))

# Wallet class map — used to resolve the correct contract from WALLET_VERSION
WALLET_CLASSES: dict[str, Any] = {"V4R2": WalletV4R2, "V5R1": WalletV5R1}

# Minimum wallet balance required to cover TON network gas fees.
MIN_TON_BALANCE: float = 0.056

# Default HTTP request timeout in seconds.
DEFAULT_TIMEOUT: float = 30.0

# Required Fragment session cookie keys
REQUIRED_COOKIE_KEYS: tuple[str, ...] = ("stel_ssid", "stel_dt", "stel_token", "stel_ton_token")

# Fragment page URLs
FRAGMENT_BASE_URL: str = "https://fragment.com"
STARS_PAGE: str = f"{FRAGMENT_BASE_URL}/stars/buy"
STARS_GIVEAWAY_PAGE: str = f"{FRAGMENT_BASE_URL}/stars/giveaway"
PREMIUM_PAGE: str = f"{FRAGMENT_BASE_URL}/premium/gift"
PREMIUM_GIVEAWAY_PAGE: str = f"{FRAGMENT_BASE_URL}/premium/giveaway"
ADS_TOPUP_PAGE: str = f"{FRAGMENT_BASE_URL}/ads/topup"
NUMBERS_PAGE: str = f"{FRAGMENT_BASE_URL}/numbers"

# Tonkeeper device fingerprint — serialized once, reused in every tx_data payload.
DEVICE: str = json.dumps(
    {
        "platform": "iphone",
        "appName": "Tonkeeper",
        "appVersion": "5.5.2",
        "maxProtocolVersion": 2,
        "features": [
            "SendTransaction",
            {"name": "SendTransaction", "maxMessages": 255},
            {"name": "SignData", "types": ["text", "binary", "cell"]},
        ],
    }
)

# Base HTTP headers — shared across all Fragment API requests.
# Each method merges these with its own "referer" and "x-aj-referer".
BASE_HEADERS: dict[str, str] = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-language": "en-US,en;q=0.9,uk;q=0.8,ru;q=0.7",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": FRAGMENT_BASE_URL,
    "priority": "u=1, i",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1"
    ),
    "x-requested-with": "XMLHttpRequest",
}
