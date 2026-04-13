from __future__ import annotations

import rookiepy

from pyfragment.types import CookieError
from pyfragment.types.constants import FRAGMENT_BASE_URL, FRAGMENT_DOMAIN, REQUIRED_COOKIE_KEYS, SUPPORTED_BROWSERS


def get_cookies_from_browser(browser: str = "chrome") -> dict[str, str]:
    """Extract Fragment session cookies directly from an installed browser.

    Reads the browser's on-disk cookie store (no extension required) and
    returns the four cookies required by :class:`~pyfragment.FragmentClient`.

    Args:
        browser: Browser name to read cookies from — case-insensitive. Supported values:
            ``"chrome"`` (default), ``"firefox"``, ``"edge"``, ``"brave"``, ``"arc"``,
            ``"opera"``, ``"opera_gx"``, ``"chromium"``, ``"chromium_based"``,
            ``"firefox_based"``, ``"vivaldi"``, ``"librewolf"``, ``"safari"``.

    Returns:
        A dict with the four required Fragment cookie keys:
        ``stel_ssid``, ``stel_dt``, ``stel_token``, ``stel_ton_token``.

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

    return {k: cookie_map[k] for k in REQUIRED_COOKIE_KEYS}
