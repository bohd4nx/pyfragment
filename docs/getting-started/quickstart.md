# Quick Start

Use this minimal example to verify that your credentials, cookies, and wallet setup are correct.

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

If this script returns wallet data, your setup is healthy.

Then move to feature pages:

- Stars: [Purchase](client/stars/purchase.md), [Giveaway](client/stars/giveaway.md)
- Premium: [Purchase](client/premium/purchase.md), [Giveaway](client/premium/giveaway.md)
- Marketplace: [Overview](client/marketplace/overview.md), Ads: [Overview](client/ads/overview.md)
- Numbers: [Anonymous Numbers](client/anonymous-numbers/overview.md)
- Utility operations: [Raw API Calls](client/raw-call.md)
