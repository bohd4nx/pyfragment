# Credentials and Cookies

This page covers the three things you need before making real requests: Tonapi key, wallet seed, and Fragment cookies.

## Tonapi key

Generate an API key at https://tonconsole.com.

## Seed phrase

Use your GRAM (ex TON) wallet mnemonic.

- **Keep it private.**
- **Never log it or commit it to git.**

## Fragment cookies

You must be logged in to Fragment.

### Option 1: automatic extraction

```python
from pyfragment import get_cookies_from_browser

cookie_result = get_cookies_from_browser("chrome")
cookies = cookie_result.cookies
```

`cookie_result` is `CookieResult`:

- `cookies`: `dict[str, str]`
- `expires`: ISO string or `None`

### Option 2: manual export

Export the four required Fragment cookies and pass them directly as dict or JSON string.

Required keys:

- `stel_ssid`
- `stel_dt`
- `stel_token`
- `stel_ton_token`

## Common auth failures

- expired session cookies,
- not logged in on fragment.com,
- missing `stel_*` keys,
- stale cookies from another browser/profile.

When this happens, re-login on fragment.com and refresh cookies first. It solves most auth issues.

## Next step

Proceed to [Quick Start](quickstart.md).
