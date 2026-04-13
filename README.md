<div align="center">
  <img src="https://www.bohd4n.dev/assets/projects/pyfragment.svg" alt="Fragment Logo" width="120" height="120" style="border-radius: 24px;">

  <h1 style="margin-top: 24px;">Fragment API</h1>

  <p style="font-size: 18px; margin-bottom: 24px;">
    <b>Async Python client for the Fragment API — a unified toolkit to manage Telegram assets: purchase Stars and Premium, top up TON and Ads balances, run giveaways, manage anonymous numbers, and explore the marketplace for usernames, numbers, and gifts.</b>
  </p>

[![PyPI version](https://img.shields.io/pypi/v/pyfragment?style=flat&color=blue)](https://pypi.org/project/pyfragment/)
[![PyPI downloads](https://img.shields.io/pypi/dm/pyfragment?style=flat&color=brightgreen)](https://pypi.org/project/pyfragment/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/github/license/bohd4nx/pyfragment?style=flat&color=lightgrey)](LICENSE)
[![Stars](https://img.shields.io/github/stars/bohd4nx/pyfragment?style=flat&color=yellow)](https://github.com/bohd4nx/pyfragment/stargazers)
[![CI](https://img.shields.io/github/actions/workflow/status/bohd4nx/pyfragment/ci.yml?style=flat&label=tests&logo=github)](https://github.com/bohd4nx/pyfragment/actions)

[Report Bug](https://github.com/bohd4nx/pyfragment/issues) · [Request Feature](https://github.com/bohd4nx/pyfragment/issues) · [**Donate TON**](https://app.tonkeeper.com/transfer/UQCppfw5DxWgdVHf3zkmZS8k1mt9oAUYxQLwq2fz3nhO8No5)

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

- **Automatically** (recommended) — use `get_cookies_from_browser()`, which reads them directly from your browser's on-disk store. No extension needed:
  ```python
  from pyfragment.utils import get_cookies_from_browser
  cookies = get_cookies_from_browser("chrome")  # or "firefox", "edge", "brave", ...
  ```
- **Manually** — install [Cookie Editor](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm) and export these four keys: `stel_ssid`, `stel_dt`, `stel_token`, `stel_ton_token`. Pass them as a `dict` or JSON string.

Refresh when you get authentication errors.

**Tonapi key** — generate at [tonconsole.com](https://tonconsole.com).

**Seed phrase** — 24-word mnemonic from your TON wallet (Tonkeeper → Settings → Backup). Never share it.

---

## Usage

```python
import asyncio
from pyfragment import (
    FragmentClient,
    FragmentError,       # base — catches everything below
    UserNotFoundError,   # username doesn't exist on Fragment
    WalletError,         # insufficient balance or misconfiguration
    CookieError,         # cookies are missing or expired
    TransactionError,    # on-chain broadcast failed
    ConfigurationError,  # invalid argument (months, amount, etc.)
    FragmentAPIError,    # unexpected Fragment API response
)


async def main() -> None:
    async with FragmentClient(
        seed="word1 word2 ... word24",  # 24-word TON wallet mnemonic
        api_key="YOUR_TONAPI_KEY",       # from tonconsole.com
        cookies={
            "stel_ssid": "...",
            "stel_dt": "...",
            "stel_token": "...",
            "stel_ton_token": "...",
        },
    ) as client:
        try:
            # Purchase 6 months of Telegram Premium
            result = await client.purchase_premium("@username", months=6)
            print(f"{result.amount} months of Premium successfully sent to {result.username} | tx: {result.transaction_id}")

            # Purchase 500 Stars
            result = await client.purchase_stars("@username", amount=500)
            print(f"{result.amount} Stars successfully sent to {result.username} | tx: {result.transaction_id}")

            # Top up 10 TON to Telegram balance
            # wallet must hold at least amount + ~0.056 TON for gas
            result = await client.topup_ton("@username", amount=10)
            print(f"{result.amount} TON successfully sent to {result.username} | tx: {result.transaction_id}")

        except UserNotFoundError:
            print(f"User was not found on fragment.com — check the username and try again.")
        except WalletError as e:
            print(f"Wallet error — insufficient balance or misconfiguration: {e}")
        except CookieError:
            print("Authentication failed — session cookies are missing or expired. Refresh them and retry.")
        except TransactionError as e:
            print(f"Transaction failed to broadcast on-chain: {e}")
        except ConfigurationError as e:
            print(f"Invalid argument: {e}")
        except FragmentAPIError as e:
            print(f"Unexpected response from Fragment API: {e}")
        except FragmentError as e:
            # catch-all for any other pyfragment error
            print(f"Unexpected error: {e}")


asyncio.run(main())
```

---

<div align="center">

### Made with ❤️ by [@bohd4nx](https://t.me/bohd4nx)

**Star ⭐ this repo if you found it useful!**

</div>
