import json
import logging
from pathlib import Path
from typing import Any

from app.core.exceptions import CookiesError

logger = logging.getLogger(__name__)

_REQUIRED_KEYS = ("stel_ssid", "stel_dt", "stel_token", "stel_ton_token")


def load_cookies() -> dict[str, Any]:
    cookies_path = Path(__file__).resolve().parents[2] / "cookies.json"

    if not cookies_path.exists():
        raise CookiesError(
            "cookies.json not found. Create it in the project root and paste your Fragment cookies."
        )

    try:
        with cookies_path.open("r", encoding="utf-8") as f:
            cookies = json.load(f)
    except Exception as exc:
        raise CookiesError(f"Failed to read cookies.json: {exc}") from exc

    missing = [k for k in _REQUIRED_KEYS if not str(cookies.get(k, "")).strip()]
    if missing:
        raise CookiesError(
            f"cookies.json is missing or has empty values for: {', '.join(missing)}. "
            "Open Fragment.com in your browser, copy fresh cookies, and update the file."
        )

    return cookies
