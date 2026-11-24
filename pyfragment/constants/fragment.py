from __future__ import annotations

FRAGMENT_BASE_URL: str = "https://fragment.com"
FRAGMENT_API_URL: str = f"{FRAGMENT_BASE_URL}/api"

STARS_PAGE: str = f"{FRAGMENT_BASE_URL}/stars/buy"
STARS_GIVEAWAY_PAGE: str = f"{FRAGMENT_BASE_URL}/stars/giveaway"
PREMIUM_PAGE: str = f"{FRAGMENT_BASE_URL}/premium/gift"
PREMIUM_GIVEAWAY_PAGE: str = f"{FRAGMENT_BASE_URL}/premium/giveaway"
STARS_HISTORY_PAGE: str = f"{FRAGMENT_BASE_URL}/stars/history"
PREMIUM_HISTORY_PAGE: str = f"{FRAGMENT_BASE_URL}/premium/history"
PROFILE_PAGE: str = f"{FRAGMENT_BASE_URL}/my/profile"
MY_USERNAMES_PAGE: str = f"{FRAGMENT_BASE_URL}/my/usernames"
MY_NUMBERS_PAGE: str = f"{FRAGMENT_BASE_URL}/my/numbers"
MY_GIFTS_PAGE: str = f"{FRAGMENT_BASE_URL}/my/gifts"
NUMBERS_PAGE: str = f"{FRAGMENT_BASE_URL}/numbers"
GIFTS_PAGE: str = f"{FRAGMENT_BASE_URL}/gifts"

# Attempts (initial try included) for a Fragment API call that hits HTTP 429
MAX_API_ATTEMPTS: int = 3

# How often to poll Fragment for its own on-chain purchase confirmation
CONFIRM_STATE_POLL_INTERVAL: float = 2.0

# Without either one every page answers as logged out (and a request lacking stel_token ends the session).
# stel_ssid and stel_dt change nothing, they are sent when given.
REQUIRED_COOKIE_KEYS: tuple[str, ...] = ("stel_token", "stel_ton_token")

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
