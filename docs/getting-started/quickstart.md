# Quick Start

Use this minimal example to verify that your credentials, cookies, and wallet setup are correct.

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
        print(wallet)

asyncio.run(main())
```

If this script returns wallet data, your setup is healthy.

Then move to feature pages:

- Stars: [Purchase](../client/stars/purchase.md), [Giveaway](../client/stars/giveaway.md)
- Premium: [Purchase](../client/premium/purchase.md), [Giveaway](../client/premium/giveaway.md)
- [Ads](../client/ads.md)
- [Anonymous Numbers](../client/anonymous-numbers.md)
- [Marketplace](../client/marketplace/overview.md)
