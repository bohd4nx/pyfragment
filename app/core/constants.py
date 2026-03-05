import json

# Fragment page URLs
STARS_PAGE:   str = "https://fragment.com/stars/buy"
PREMIUM_PAGE: str = "https://fragment.com/premium/gift"
ADS_PAGE:     str = "https://fragment.com/ads/topup"

# Tonkeeper device fingerprint — serialized once, reused in every tx_data payload.
DEVICE: str = json.dumps({
    "platform":           "iphone",
    "appName":            "Tonkeeper",
    "appVersion":         "5.5.2",
    "maxProtocolVersion": 2,
    "features": [
        "SendTransaction",
        {"name": "SendTransaction", "maxMessages": 255},
        {"name": "SignData", "types": ["text", "binary", "cell"]},
    ],
})

# Base HTTP headers — shared across all Fragment API requests.
# Each method merges these with its own "referer" and "x-aj-referer".
BASE_HEADERS: dict[str, str] = {
    "accept":           "application/json, text/javascript, */*; q=0.01",
    "accept-language":  "en-US,en;q=0.9,uk;q=0.8,ru;q=0.7",
    "content-type":     "application/x-www-form-urlencoded; charset=UTF-8",
    "origin":           "https://fragment.com",
    "priority":         "u=1, i",
    "sec-fetch-dest":   "empty",
    "sec-fetch-mode":   "cors",
    "sec-fetch-site":   "same-origin",
    "user-agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1"
    ),
    "x-requested-with": "XMLHttpRequest",
}
