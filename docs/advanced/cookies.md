# Cookie Extraction Details

`get_cookies_from_browser(browser)` reads Fragment cookies from local browser storage (via `rookiepy`).

This is the fastest way to start when you do not want manual cookie export.

Supported browsers are defined in constants and include:

- chrome, firefox, edge, brave,
- arc, opera, opera_gx,
- safari, vivaldi,
- chromium variants.

Validation includes:

- required key presence,
- non-empty values,
- optional expiration check for `stel_ssid`.

**If any required cookie is empty or missing, extraction is treated as failed.**

If extraction fails, `CookieError` is raised with actionable details.

Use [Credentials and Cookies](../getting-started/credentials-and-cookies.md) for setup-first instructions.
