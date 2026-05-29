from __future__ import annotations

import importlib
from datetime import datetime, timezone
from typing import Any

from pyfragment.core.constants import FRAGMENT_BASE_URL, FRAGMENT_DOMAIN, REQUIRED_COOKIE_KEYS
from pyfragment.exceptions import CookieError
from pyfragment.models.cookies import CookieResult
from pyfragment.models.enums import SupportedBrowser

try:
    import rookiepy
except Exception:  # noqa: BLE001
    rookiepy = None  # type: ignore[assignment]


def get_cookies_from_browser(browser: str = "chrome") -> CookieResult:
    global rookiepy

    key = browser.lower()
    if not any(key == m for m in SupportedBrowser):
        supported = ", ".join(sorted(b.value for b in SupportedBrowser))
        raise CookieError(CookieError.UNSUPPORTED_BROWSER.format(browser=browser, supported=supported))

    try:
        if rookiepy is None:
            rookiepy = importlib.import_module("rookiepy")

        jar: list[dict[str, Any]] = getattr(rookiepy, key)([FRAGMENT_DOMAIN])
    except Exception as exc:
        raise CookieError(CookieError.BROWSER_READ_FAILED.format(browser=browser, exc=exc, url=FRAGMENT_BASE_URL)) from exc

    cookie_map: dict[str, str] = {c["name"]: c["value"] for c in jar if c.get("name") and c.get("value")}

    missing = [k for k in REQUIRED_COOKIE_KEYS if not str(cookie_map.get(k, "")).strip()]
    if missing:
        raise CookieError(CookieError.MISSING_BROWSER_KEYS.format(browser=browser, keys=missing, url=FRAGMENT_BASE_URL))

    expires_iso: str | None = None
    for cookie in jar:
        if cookie.get("name") == "stel_ssid":
            raw = cookie.get("expires")
            if isinstance(raw, (int, float)):
                expires_iso = datetime.fromtimestamp(raw, tz=timezone.utc).isoformat()
            elif isinstance(raw, str) and raw:
                for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
                    try:
                        expires_iso = datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc).isoformat()
                        break
                    except ValueError:
                        continue
            break

    if expires_iso:
        expires_dt = datetime.fromisoformat(expires_iso)
        if expires_dt < datetime.now(timezone.utc):
            raise CookieError(CookieError.EXPIRED.format(expires=expires_iso))

    return CookieResult(cookies={k: cookie_map[k] for k in REQUIRED_COOKIE_KEYS}, expires=expires_iso)
