from __future__ import annotations

from datetime import datetime, timezone

import rookiepy

from pyfragment.types import CookieError, CookieResult
from pyfragment.types.constants import FRAGMENT_BASE_URL, FRAGMENT_DOMAIN, REQUIRED_COOKIE_KEYS, SUPPORTED_BROWSERS


def get_cookies_from_browser(browser: str = "chrome") -> CookieResult:
    """Extract Fragment session cookies directly from an installed browser.

    Reads the browser's on-disk cookie store (no extension required) and
    returns the four cookies required by :class:`~pyfragment.FragmentClient`
    along with the session expiry timestamp.

    Args:
        browser: Browser name to read cookies from — case-insensitive. Supported values:
            ``"chrome"`` (default), ``"firefox"``, ``"edge"``, ``"brave"``, ``"arc"``,
            ``"opera"``, ``"opera_gx"``, ``"chromium"``, ``"chromium_based"``,
            ``"firefox_based"``, ``"vivaldi"``, ``"librewolf"``, ``"safari"``.

    Returns:
        :class:`CookieResult` with ``.cookies`` (dict) and ``.expires`` (ISO 8601 string or ``None``).

    Raises:
        CookieError: If the browser is not supported, cookies cannot be read,
            or required keys are missing.
    """
    key = browser.lower()
    if key not in SUPPORTED_BROWSERS:
        supported = ", ".join(sorted(SUPPORTED_BROWSERS))
        raise CookieError(CookieError.UNSUPPORTED_BROWSER.format(browser=browser, supported=supported))

    try:
        jar: list[dict] = getattr(rookiepy, key)([FRAGMENT_DOMAIN])
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

    return CookieResult(
        cookies={k: cookie_map[k] for k in REQUIRED_COOKIE_KEYS},
        expires=expires_iso,
    )
