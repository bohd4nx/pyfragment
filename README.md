<div align="center">
  <img src="fragment.svg" alt="Fragment Logo" width="120" height="120" style="border-radius: 24px;">

  <h1 style="margin-top: 24px;">💎 Fragment API</h1>

  <p style="font-size: 18px; margin-bottom: 24px;">
    <b>Python library for the Fragment.com API — gift Telegram Stars, Premium, and top up TON Ads balance.</b>
  </p>

[![PyPI version](https://img.shields.io/pypi/v/fragmentapi?style=flat&color=blue)](https://pypi.org/project/fragmentapi/)
[![PyPI downloads](https://img.shields.io/pypi/dm/fragmentapi?style=flat&color=brightgreen)](https://pypi.org/project/fragmentapi/)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/github/license/bohd4nx/FragmentAPI?style=flat&color=lightgrey)](LICENSE)
[![Stars](https://img.shields.io/github/stars/bohd4nx/FragmentAPI?style=flat&color=yellow)](https://github.com/bohd4nx/FragmentAPI/stargazers)
[![CI](https://img.shields.io/github/actions/workflow/status/bohd4nx/FragmentAPI/tests.yml?style=flat&label=tests&logo=github)](https://github.com/bohd4nx/FragmentAPI/actions)

[Report Bug](https://github.com/bohd4nx/FragmentAPI/issues) · [Request Feature](https://github.com/bohd4nx/FragmentAPI/issues) · [**Donate TON**](https://app.tonkeeper.com/transfer/UQCppfw5DxWgdVHf3zkmZS8k1mt9oAUYxQLwq2fz3nhO8No5)

</div>

---

## ✨ Features

- 💰 **TON Advertisement Topups** — Top up Telegram Ads balance (1–1,000,000,000 TON)
- 👑 **Telegram Premium Gifts** — Gift Premium to any user (3, 6, or 12 months)
- ⭐ **Telegram Stars Purchases** — Gift Stars to any Telegram user (50–1,000,000 Stars)
- 🔐 **Multi-wallet support** — V4R2 and V5R1 wallet contract versions
- ⚡ **Async-first** — Built on `httpx` and `asyncio`

---

## 📦 Installation

```bash
pip install fragmentapi
```

Requires **Python 3.12+**.

---

## 🚀 Quick Start

```python
import asyncio
from fragmentapi import FragmentClient

client = FragmentClient(
    seed="word1 word2 ... word24",
    api_key="YOUR_TONAPI_KEY",
    cookies={
        "stel_ssid": "...",
        "stel_dt": "...",
        "stel_token": "...",
        "stel_ton_token": "...",
    },
)

async def main():
    # Gift 6 months of Telegram Premium
    result = await client.gift_premium("@username", months=6)
    print(result.transaction_id)

    # Gift 500 Stars
    result = await client.gift_stars("@username", amount=500)
    print(result.transaction_id)

    # Top up 10 TON to Ads balance
    result = await client.topup_ton("@username", amount=10)
    print(result.transaction_id)

asyncio.run(main())
```

See the [`examples/`](examples/) folder for ready-to-run scripts.

---

## 🔧 Configuration

### `FragmentClient` parameters

| Parameter        | Type          | Required | Default  | Description                                              |
| ---------------- | ------------- | -------- | -------- | -------------------------------------------------------- |
| `seed`           | `str`         | ✅        | —        | 24-word TON wallet mnemonic phrase                       |
| `api_key`        | `str`         | ✅        | —        | Tonapi key from [tonconsole.com](https://tonconsole.com) |
| `cookies`        | `dict \| str` | ✅        | —        | Fragment session cookies (dict or JSON string)           |
| `wallet_version` | `str`         | ❌        | `"V5R1"` | Wallet contract version: `"V4R2"` or `"V5R1"`            |

### Methods

> Usernames can be passed with or without `@`.

| Method                                             | Returns          | Description                        | Limits                    |
| -------------------------------------------------- | ---------------- | ---------------------------------- | ------------------------- |
| `gift_premium(username, months, show_sender=True)` | `PremiumResult`  | Gift Telegram Premium subscription | `months`: 3, 6, or 12     |
| `gift_stars(username, amount, show_sender=True)`   | `StarsResult`    | Gift Telegram Stars                | `amount`: 50–1,000,000    |
| `topup_ton(username, amount, show_sender=True)`    | `AdsTopupResult` | Top up Telegram Ads balance        | `amount`: 1–1,000,000,000 |

---

## ⚙️ Getting Required Credentials

### 🍪 Fragment.com Cookies

**Prerequisites**: Log in to [fragment.com](https://fragment.com), connect your TON wallet.

1. Install [Cookie Editor](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm)
2. Open [fragment.com](https://fragment.com) while logged in
3. Click the extension → **Export** → **JSON**
4. Extract these four fields:

```json
{
  "stel_ssid": "...",
  "stel_dt": "...",
  "stel_token": "...",
  "stel_ton_token": "..."
}
```

> ⚠️ Cookies expire. Refresh them if you start getting `FragmentPageError` or auth errors.

### 🔑 Tonapi Key

1. Go to [tonconsole.com](https://tonconsole.com)
2. Register and generate a new API key
3. Pass it as `api_key` to `FragmentClient`

### 🌱 Wallet Seed Phrase

If you don't have a TON wallet, create one in [Tonkeeper](https://tonkeeper.com).  
Go to **Settings → Backup** → copy the 24 words.

> ⚠️ Never share your seed phrase. Store it offline.

### 🔐 Wallet Version

| Version | Use when                                                       |
| ------- | -------------------------------------------------------------- |
| `V5R1`  | Default — Tonkeeper / MyTonWallet (wallets created after 2024) |
| `V4R2`  | Older Tonkeeper or hardware wallets                            |

---

## 🗂️ Error Handling

All exceptions inherit from `FragmentError` — see [`fragmentapi/types/exceptions.py`](fragmentapi/types/exceptions.py) for the full list.

```python
from fragmentapi import FragmentClient, UserNotFoundError, ConfigurationError, WalletError

try:
    result = await client.gift_stars("@unknown", amount=100)
except UserNotFoundError:
    print("User not found on Fragment")
except WalletError as e:
    print(f"Wallet issue: {e}")
except ConfigurationError as e:
    print(f"Bad params: {e}")
```

---

<div align="center">

### Made with ❤️ by [@bohd4nx](https://t.me/bohd4nx)

**Star ⭐ this repo if you found it useful!**

</div>
