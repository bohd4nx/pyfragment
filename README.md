<div align="center">
  <img src="https://www.bohd4n.dev/assets/projects/pyfragment.svg" alt="pyfragment" width="96" height="96" style="border-radius: 20px;"><br><br>

# pyfragment

[![PyPI](https://img.shields.io/pypi/v/pyfragment?style=flat&color=blue&label=PyPI)](https://pypi.org/project/pyfragment/)
[![Downloads](https://img.shields.io/pepy/dt/pyfragment?style=flat&color=blue&label=Downloads)](https://pepy.tech/projects/pyfragment)
[![Python](https://img.shields.io/pypi/pyversions/pyfragment?style=flat&color=blue&label=Python)](https://python.org)
[![Tests](https://img.shields.io/github/actions/workflow/status/bohd4nx/pyfragment/ci.yml?style=flat&label=Tests&logo=github)](https://github.com/bohd4nx/pyfragment/actions)
[![License](https://img.shields.io/github/license/bohd4nx/pyfragment?style=flat&color=blue&label=License)](LICENSE)

Async Python client for the **[Fragment](https://fragment.com)** marketplace API.
Buy Stars & Premium, run giveaways, top up GRAM (ex TON) and Ads balances,
manage anonymous numbers, and search Fragment listings.

**[Documentation](https://bohd4nx.gitbook.io/pyfragment/)** · **[Examples](https://github.com/bohd4nx/pyfragment/tree/master/examples)** · **[Changelog](CHANGELOG.md)** · **[Donate GRAM](https://app.tonkeeper.com/transfer/UQCppfw5DxWgdVHf3zkmZS8k1mt9oAUYxQLwq2fz3nhO8No5)**

</div>

> **Disclaimer:** This project is not affiliated with [Fragment](https://fragment.com) or [Telegram](https://telegram.org).

---

## Installation

```bash
pip install pyfragment
```

```bash
# Latest dev build
pip install git+https://github.com/bohd4nx/pyfragment.git@dev
```

---

## Quick Start

```python
import asyncio

from pyfragment import FragmentClient
from pyfragment.enums import PaymentMethod


async def main() -> None:
    async with FragmentClient(
        seed="word1 word2 ... word24",
        api_key="YOUR_API_KEY",  # tonconsole.com (tonapi, default) or t.me/toncenter
        cookies={
            "stel_ssid": "...",
            "stel_dt": "...",
            "stel_token": "...",
            "stel_ton_token": "...",
        },
        wallet_version="V5R1",   # or "V4R2", "HighloadV2", "HighloadV3R1"
        api_provider="tonapi",   # or "toncenter"
    ) as client:
        wallet = await client.get_wallet()
        print(f"GRAM: {wallet.gram_balance} | USDT: {wallet.usdt_balance}")

        recipient = "https://t.me/username"  # also: @username, username

        stars = await client.purchase_stars(recipient, amount=500, payment_method=PaymentMethod.USDT_GRAM)
        print(f"Sent {stars.amount} Stars to {stars.username} | tx: {stars.transaction_id}")

        premium = await client.purchase_premium(recipient, months=6, payment_method=PaymentMethod.GRAM)
        print(f"Sent Premium {premium.amount}m to {premium.username} | tx: {premium.transaction_id}")


asyncio.run(main())
```

---

## Configuration

| Parameter        | Type          | Default     | Description                                                                    |
| ---------------- | ------------- | ----------- | ------------------------------------------------------------------------------ |
| `seed`           | `str`         | —           | 12- or 24-word GRAM (ex TON) wallet mnemonic                                   |
| `api_key`        | `str`         | —           | API key for the chosen provider (see `api_provider`)                           |
| `cookies`        | `dict \| str` | —           | Fragment session cookies                                                       |
| `wallet_version` | `str`         | `"V5R1"`    | `"V4R2"` or `"V5R1"` — also accepts `WalletVersion` literal                   |
| `api_provider`   | `str`         | `"tonapi"`  | `"tonapi"` ([tonconsole.com](https://tonconsole.com)) or `"toncenter"` ([t.me/toncenter](https://t.me/toncenter)) |
| `timeout`        | `float`       | `30.0`      | HTTP request timeout in seconds                                                |

---

## Credentials

### Fragment cookies

Log in to [fragment.com](https://fragment.com) and connect your GRAM (ex TON) wallet.

**Automatically** (recommended) — reads directly from your browser, no extension needed:

```bash
pip install "pyfragment[browser]"
```

```python
from pyfragment import get_cookies_from_browser

result = get_cookies_from_browser("chrome")  # firefox, edge, brave, ...
# result.cookies  — dict[str, str] ready to pass to FragmentClient
# result.expires  — ISO 8601 expiry of stel_ssid, or None for session cookies
```

**Manually** — use [Cookie Editor](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm) and export: `stel_ssid`, `stel_dt`, `stel_token`, `stel_ton_token`. Pass as a `dict` or JSON string.

Refresh cookies when you get authentication errors.

### Tonapi key

Generate at [tonconsole.com](https://tonconsole.com).

### Seed phrase

12- or 24-word mnemonic from your GRAM (ex TON) wallet (**Tonkeeper → Settings → Backup**). Never share it.

---

## Logging

`pyfragment` uses the standard `logging` module under the `pyfragment` namespace and is silent by default:

```python
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger("pyfragment").setLevel(logging.DEBUG)  # for detailed request logs
```

---

## Error Handling

All exceptions inherit from `FragmentError`:

```python
from pyfragment import (
    ConfigurationError,   # invalid arguments (amount, months, payment_method…)
    UserNotFoundError,    # recipient not found on Fragment
    WalletError,          # insufficient GRAM (ex TON) or USDT balance
    TransactionError,     # broadcast failed, duplicate seqno, invalid payload
    FragmentAPIError,     # Fragment API returned an error response
    FragmentPageError,    # page fetch or hash extraction failed
    AnonymousNumberError, # number not owned, wrong state, login code issues
    CookieError,          # missing or malformed session cookies
    ParseError,           # failed to decode Fragment payload
    VerificationError,    # on-chain verification step failed
    OperationError,       # generic operation-level failure
    UnexpectedError,      # unexpected API response structure
)
```

---

<div align="center">

Made with ❤️ by [@bohd4nx](https://t.me/bohd4nx) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md)

**Star ⭐ if you found it useful**

</div>
