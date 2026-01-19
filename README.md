<div align="center">
  <img src="fragment.svg" alt="Fragment Logo" width="120" height="120" style="border-radius: 24px;">

  <h1 style="margin-top: 24px;">💎 Fragment API by @bohd4nx</h1>

  <p style="font-size: 18px; margin-bottom: 24px;">
    <b>Automate TON topups, Telegram Premium purchases, and Stars transactions via Fragment.com</b>
  </p>

[Report Bug](https://github.com/bohd4nx/fragmentapi/issues) · [Request Feature](https://github.com/bohd4nx/fragmentapi/issues) · [
**Donate TON**](https://app.tonkeeper.com/transfer/UQCppfw5DxWgdVHf3zkmZS8k1mt9oAUYxQLwq2fz3nhO8No5)

</div>

---

## ✨ Features

- 💰 **TON Advertisement Topups** - Send TON for advertising campaigns and purchasing gifts (1-1,000,000,000 TON)
- 👑 **Telegram Premium Gifts** - Purchase Premium subscriptions (3, 6, or 12 months)
- ⭐ **Telegram Stars Purchases** - Buy Stars for users (50-1,000,000 Stars)

## 🚀 Quick Start

### 1. Installation

```bash
git clone https://github.com/bohd4nx/FragmentAPI.git
cd FragmentAPI
pip install -r requirements.txt
```

### 2. Configuration

Copy example configuration and edit:

```bash
cp .env.example .env
```

Edit `.env` file:

```env
SEED=word1 word2 word3 ... word24

API_KEY=your_ton_api_key_here
```

### 3. Getting Required Data

#### 🍪 Fragment.com Cookies

**Prerequisites**: Login to your Telegram account and connect the TON wallet you want to use for payments.

1. **Install Cookie Editor Extension**:

    - Download
      from [Chrome Web Store](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm)
    - Add extension to your browser

2. **Extract Cookies**:
    - Open [Fragment.com](https://fragment.com) and ensure you're logged in
    - Refresh the page completely
    - Click on the Cookie Editor extension icon
    - Click **"Export"** button
    - Select **"Header String"** format
    - Copy the result and split it into JSON fields in `cookies.json`

**Expected format** (`cookies.json` in project root):

```json
{
  "stel_ssid": "<SSID>",
  "stel_dt": "<STEL_DT>",
  "stel_token": "<TOKEN>",
  "stel_ton_token": "<TON_TOKEN>"
}
```

#### 🔐 TON Wallet Seed Phrase

**If you don't have a TON wallet yet**:

1. **Download Tonkeeper**:

    - iOS: [App Store](https://apps.apple.com/app/tonkeeper/id1587742107)
    - Android: [Google Play](https://play.google.com/store/apps/details?id=com.ton_keeper)

2. **Create New Wallet**:

    - Open Tonkeeper app
    - Tap **"Create New Wallet"**
    - **IMPORTANT**: Write down your 24-word seed phrase on paper
    - Store it securely - never share with anyone!
    - Complete wallet setup

3. **Get Your Seed Phrase**:
    - If you already have a wallet, go to Settings → Backup
    - Enter your passcode
    - Copy the 24 words → paste to `SEED` in your `.env` file

**Format**: `word1 word2 word3 ... word24`

#### 🔗 Fragment Hash

Hash is fetched automatically from Fragment pages at runtime. You no longer need to add `HASH` to `.env`.

#### 🔑 TON API Key

1. **Get API Key**:
    - Visit [TON Console](https://tonconsole.com)
    - Create account and login
    - Generate new API key
    - Copy the key → paste to `API_KEY` in your `.env` file

**Alternative**: You can also use [TON API](https://tonapi.io) for getting API key.

### 4. Usage

#### Run Examples

```bash
python main.py
```

#### Programmatic Usage

```python
from app.methods import FragmentTon, FragmentPremium, FragmentStars

# TON topup for ads
ton_client = FragmentTon()
result = await ton_client.topup_ton("@username", 5)

# Premium purchase
premium_client = FragmentPremium()
result = await premium_client.buy_premium("@username", 6)

# Stars purchase
stars_client = FragmentStars()
result = await stars_client.buy_stars("@username", 50)
```

### Supported Operations

| Operation          | Method                          | Parameters             | Limits              |
|--------------------|---------------------------------|------------------------|---------------------|
| **TON Topup**      | `topup_ton(username, amount)`   | Username, TON amount   | 1-1,000,000,000 TON |
| **Premium Gift**   | `buy_premium(username, months)` | Username, duration     | 3, 6, or 12 months  |
| **Stars Purchase** | `buy_stars(username, amount)`   | Username, Stars amount | 50-1,000,000 Stars  |

### Username Formats

All methods accept various username formats:

- `@username` (with @)
- `username` (without @)

<div align="center">

### Made with ❤️ by [@bohd4nx](https://t.me/bohd4nx)

**Star ⭐ this repo if you found it useful!**

</div>
