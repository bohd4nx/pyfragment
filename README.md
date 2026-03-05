<div align="center">
  <img src="fragment.svg" alt="Fragment Logo" width="120" height="120" style="border-radius: 24px;">

  <h1 style="margin-top: 24px;">💎 Fragment API by @bohd4nx</h1>

  <p style="font-size: 18px; margin-bottom: 24px;">
    <b>Automate TON topups, Telegram Premium purchases, and Stars transactions via Fragment.com</b>
  </p>

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![tonutils](https://img.shields.io/badge/tonutils-2.0.0-0098EA?style=flat&logo=ton&logoColor=white)](https://github.com/nessshon/tonutils)
[![Stars](https://img.shields.io/github/stars/bohd4nx/FragmentAPI?style=flat&color=yellow)](https://github.com/bohd4nx/FragmentAPI/stargazers)
[![Issues](https://img.shields.io/github/issues/bohd4nx/FragmentAPI?style=flat&color=red)](https://github.com/bohd4nx/FragmentAPI/issues)
[![CI](https://img.shields.io/github/actions/workflow/status/bohd4nx/FragmentAPI/tests.yml?style=flat&label=tests&logo=github)](https://github.com/bohd4nx/FragmentAPI/actions)

[Report Bug](https://github.com/bohd4nx/fragmentapi/issues) · [Request Feature](https://github.com/bohd4nx/fragmentapi/issues) · [**Donate TON**](https://app.tonkeeper.com/transfer/UQCppfw5DxWgdVHf3zkmZS8k1mt9oAUYxQLwq2fz3nhO8No5)

</div>

---

## ✨ Features

- 💰 **TON Advertisement Topups** — Send TON directly to Fragment ad accounts (1–1,000,000,000 TON)
- 👑 **Telegram Premium Gifts** — Purchase Premium subscriptions for any user (3, 6, or 12 months)
- ⭐ **Telegram Stars Purchases** — Buy Stars and send them to any Telegram user (50–1,000,000 Stars)
- 🔐 **Multi-wallet support** — Configurable wallet contract version (V4R2 / V5R1)

## 🚀 Quick Start

### 1. Installation

```bash
git clone https://github.com/bohd4nx/FragmentAPI.git
cd FragmentAPI
pip install -r requirements.txt
```

### 2. Configuration

```bash
cp .env.example .env
cp cookies.example.json cookies.json
```

Edit `.env`:

```env
# 24-word TON wallet seed phrase
SEED = word1 word2 word3 ... word24

# API key from @tonapibot on Telegram
API_KEY = your_tonapi_key_here

# Wallet contract version: V4R2 or V5R1 (default: V5R1)
WALLET_VERSION = V5R1
```

### 3. Getting Required Data

#### 🍪 Fragment.com Cookies

**Prerequisites**: Log in to Telegram on Fragment and connect the TON wallet you'll use for payments.

1. Install [Cookie Editor](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm) extension
2. Open [fragment.com](https://fragment.com) and make sure you're logged in
3. Click the Cookie Editor icon → **Export** → **Header String**
4. Split the result into the four fields in `cookies.json`:

```json
{
  "stel_ssid": "...",
  "stel_dt": "...",
  "stel_token": "...",
  "stel_ton_token": "..."
}
```

#### 🔐 TON Wallet Seed Phrase

If you don't have a TON wallet, create one in [Tonkeeper](https://tonkeeper.com) (iOS / Android).  
Go to **Settings → Backup**, copy the 24 words and paste them into `SEED` in `.env`.

> ⚠️ Never share your seed phrase with anyone. Store it offline.

#### 🔑 TON API Key

1. Go to [tonconsole.com](https://tonconsole.com)
2. Create an account and log in
3. Generate a new API key
4. Paste it into `API_KEY` in `.env`

#### 🔐 Wallet Version

| Version | Use when                                                       |
| ------- | -------------------------------------------------------------- |
| `V5R1`  | Default — Tonkeeper / MyTonWallet (wallets created after 2024) |
| `V4R2`  | Older Tonkeeper wallets                                        |

Not sure? Run this to check which address matches your wallet:

```bash
python3 -c "
import asyncio
from tonutils.clients import TonapiClient
from tonutils.contracts.wallet import WalletV4R2, WalletV5R1
from tonutils.types import NetworkGlobalID
from app.core import config

client = TonapiClient(network=NetworkGlobalID.MAINNET, api_key=config.API_KEY)
w4, _, _, _ = WalletV4R2.from_mnemonic(client=client, mnemonic=config.SEED)
w5, _, _, _ = WalletV5R1.from_mnemonic(client=client, mnemonic=config.SEED)
print('V4R2:', w4.address.to_str(True, True))
print('V5R1:', w5.address.to_str(True, True))
"
```

### 4. Usage

#### Run Examples

```bash
python main.py
```

#### Programmatic Usage

```python
import asyncio
from app.methods import topup_ton, buy_premium, buy_stars

async def main():
    # Send 10 TON to @username
    result = await topup_ton("@username", 10)
    print(result)

    # Gift 6 months of Telegram Premium
    result = await buy_premium("@username", 6)
    print(result)

    # Buy 500 Stars for @username
    result = await buy_stars("@username", 500)
    print(result)

asyncio.run(main())
```

**Return format** (on success):

```python
{
    "success": True,
    "data": {
        "transaction_id": "<TL-B ExternalMessage ...>",
        "username": "@username",
        "amount": 10,          # or "months" for Premium
        "timestamp": 1741234567
    }
}
```

**Return format** (on failure):

```python
{
    "success": False,
    "error": "Telegram user '@unknown' was not found on Fragment."
}
```

### Supported Operations

| Operation          | Function                        | Parameters             | Limits              |
| ------------------ | ------------------------------- | ---------------------- | ------------------- |
| **TON Topup**      | `topup_ton(username, amount)`   | Username, TON amount   | 1–1,000,000,000 TON |
| **Premium Gift**   | `buy_premium(username, months)` | Username, duration     | 3, 6, or 12 months  |
| **Stars Purchase** | `buy_stars(username, amount)`   | Username, Stars amount | 50–1,000,000 Stars  |

Usernames can be passed with or without `@`.

<div align="center">

### Made with ❤️ by [@bohd4nx](https://t.me/bohd4nx)

**Star ⭐ this repo if you found it useful!**

</div>
