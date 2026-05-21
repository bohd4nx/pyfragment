<div align="center">
  <img src="https://www.bohd4n.dev/assets/projects/pyfragment.svg" alt="Fragment Logo" width="120" height="120" style="border-radius: 24px;">

  <h1 style="margin-top: 24px;">Fragment API</h1>

  <p style="font-size: 18px; margin-bottom: 24px;">
    <b>Async Python client for the Fragment API. Buy Stars and Premium, top up TON and Ads balances, run giveaways, manage anonymous numbers, and search Fragment listings.</b>
  </p>

[![PyPI version](https://img.shields.io/pypi/v/pyfragment?style=flat&color=blue)](https://pypi.org/project/pyfragment/)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/pyfragment?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/pyfragment)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Tests](https://img.shields.io/github/actions/workflow/status/bohd4nx/pyfragment/ci.yml?style=flat&label=tests&logo=github)](https://github.com/bohd4nx/pyfragment/actions)
[![License](https://img.shields.io/github/license/bohd4nx/pyfragment?style=flat&color=green)](https://github.com/bohd4nx/pyfragment/blob/master/LICENSE)

[Documentation](https://bohd4nx.gitbook.io/pyfragment/) · [Report Bug](https://github.com/bohd4nx/pyfragment/issues) · [Request Feature](https://github.com/bohd4nx/pyfragment/issues) · [**Donate TON**](https://app.tonkeeper.com/transfer/UQCppfw5DxWgdVHf3zkmZS8k1mt9oAUYxQLwq2fz3nhO8No5)

</div>

> **Disclaimer:** This project is not affiliated with, endorsed by, or in any way officially connected with [Fragment](https://fragment.com) or [Telegram](https://telegram.org).

---

## Installation

```bash
pip install pyfragment
```

To install the latest unreleased changes from the `dev` branch:

```bash
pip install git+https://github.com/bohd4nx/pyfragment.git@dev
```

Requires Python 3.10+.

---

## Configuration

| Parameter        | Type          | Default  | Description                                              |
| ---------------- | ------------- | -------- | -------------------------------------------------------- |
| `seed`           | `str`         | —        | 24-word TON wallet mnemonic                              |
| `api_key`        | `str`         | —        | Tonapi key from [tonconsole.com](https://tonconsole.com) |
| `cookies`        | `dict \| str` | —        | Fragment session cookies                                 |
| `wallet_version` | `str`         | `"V5R1"` | `"V4R2"` or `"V5R1"`                                     |
| `timeout`        | `float`       | `30.0`   | HTTP request timeout in seconds                          |

---

## Credentials

**Fragment cookies** — log in to [fragment.com](https://fragment.com) and connect your TON wallet. You can get cookies in two ways:

- **Automatically** (recommended) — install the optional browser extra and use `get_cookies_from_browser()`, which reads them directly from your browser's on-disk store. No extension needed:

  ```bash
  pip install "pyfragment[browser]"
  ```

  ```python
  from pyfragment import get_cookies_from_browser

  result = get_cookies_from_browser("chrome")  # or "firefox", "edge", "brave", ...
  # result.cookies — dict[str, str] to pass to FragmentClient
  # result.expires — ISO 8601 expiry of stel_ssid, or None for session cookies
  ```

- **Manually** — install [Cookie Editor](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm) and export these four keys: `stel_ssid`, `stel_dt`, `stel_token`, `stel_ton_token`. Pass them as a `dict` or JSON string.

Refresh when you get authentication errors.

**Tonapi key** — generate at [tonconsole.com](https://tonconsole.com).

**Seed phrase** — 24-word mnemonic from your TON wallet (Tonkeeper → Settings → Backup). Never share it.

---

## Usage

```python
import asyncio
from pyfragment import FragmentClient


async def main() -> None:
    async with FragmentClient(
        seed="word1 word2 ... word24",
        api_key="YOUR_TONAPI_KEY",
        cookies={
            "stel_ssid": "...",
            "stel_dt": "...",
            "stel_token": "...",
            "stel_ton_token": "...",
        },
    ) as client:
        wallet = await client.get_wallet()
        print(f"Wallet: {wallet.address} | TON: {wallet.ton_balance} | USDT: {wallet.usdt_balance}")

        recipient = "https://t.me/username"  # also supports: @username, username

        stars = await client.purchase_stars(recipient, amount=500, payment_method="usdt_ton")
        print(f"Stars sent: {stars.amount} to {stars.username} | tx: {stars.transaction_id}")

        premium = await client.purchase_premium(recipient, months=6, payment_method="ton")
        print(f"Premium sent: {premium.amount} months to {premium.username} | tx: {premium.transaction_id}")


asyncio.run(main())
```

Full runnable examples:

- https://github.com/bohd4nx/pyfragment/tree/master/examples

Payload debug/decode helper (thanks):

- https://ton-cell-abi-viewer.vercel.app/

---

<div align="center">

### Made with ❤️ by [@bohd4nx](https://t.me/bohd4nx)

**Star ⭐ this repo if you found it useful!**

</div>
