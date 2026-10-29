<div align="center">
  <img src="icon.svg" alt="pyfragment" width="96" height="96" style="border-radius: 20px;"><br><br>

# pyfragment

[![PyPI](https://img.shields.io/pypi/v/pyfragment?style=flat&color=blue&label=PyPI)](https://pypi.org/project/pyfragment/)
[![Downloads](https://img.shields.io/pepy/dt/pyfragment?style=flat&color=blue&label=Downloads)](https://pepy.tech/projects/pyfragment)
[![Python](https://img.shields.io/pypi/pyversions/pyfragment?style=flat&color=blue&label=Python)](https://python.org)
[![Tests](https://img.shields.io/github/actions/workflow/status/bohd4nx/pyfragment/ci.yml?style=flat&label=Tests&logo=github)](https://github.com/bohd4nx/pyfragment/actions)
[![License](https://img.shields.io/github/license/bohd4nx/pyfragment?style=flat&color=blue&label=License)](LICENSE)

Async Python client for the **[Fragment.com](https://fragment.com)** marketplace API.

**[Documentation](https://bohd4nx.gitbook.io/pyfragment/)** · **[Examples](https://github.com/bohd4nx/pyfragment/tree/master/examples)**

</div>

> **Disclaimer:** This project is not affiliated with [Fragment](https://fragment.com) or [Telegram](https://telegram.org).

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
        api_key="YOUR_API_KEY",
        cookies={"stel_ssid": "...", "stel_dt": "...", "stel_token": "...", "stel_ton_token": "..."},
    ) as client:
        wallet = await client.get_wallet()
        print("GRAM: %s | USDT: %s" % (wallet.gram_balance, wallet.usdt_balance))

        stars = await client.purchase_stars("@username", amount=500, payment_method=PaymentMethod.USDT_GRAM)
        print("Sent %s Stars to %s | tx: %s" % (stars.amount, stars.username, stars.transaction_id))

        premium = await client.purchase_premium("@username", months=6, payment_method=PaymentMethod.GRAM)
        print("Sent Premium %sm to %s | tx: %s" % (premium.amount, premium.username, premium.transaction_id))


asyncio.run(main())
```

## Wallets

| Wallet                                       | `wallet_version`                   | `mnemonic_type`       |
| -------------------------------------------- | ---------------------------------- | --------------------- |
| Tonkeeper, MyTonWallet and other TON wallets | `"V5R1"` (default) or `"V4R2"`     | `"ton"` (default)     |
| Multichain wallets (BIP-39 phrase)           | `"V5R1"` or `"V4R2"`               | `"multichain"`        |
| Telegram Wallet (self-custodial)             | `"TG"`                             | always `"multichain"` |
| Highload wallets                             | `"HighloadV2"` or `"HighloadV3R1"` | either                |

Check that `get_wallet().address` is the address your wallet app shows before paying from a new configuration.

## Failures and money

A purchase returns once its payment is on-chain. A transfer is signed and sent once (never a second payment), and it
expires within a minute, so the library can always tell whether it paid. Retrying failed calls is up to you. Every error has
`retryable`: `True` means nothing was paid. Only a `BroadcastError` with `retryable=False` (the wallet history couldn't
be read) leaves the payment unchecked:

```python
from datetime import UTC, datetime

from pyfragment import BroadcastError

started = datetime.now(UTC)
try:
    stars = await client.purchase_stars("@username", amount=500)
except BroadcastError as error:
    if not error.retryable:
        transfer = await client.find_transfer(msg_hash=error.transfer.msg_hash, since=started)
        print("paid" if transfer and transfer.success else "not paid")
```

<div align="center">

[Changelog](CHANGELOG.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md)

</div>
