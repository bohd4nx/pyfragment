"""
Example: pay for many different purchases at once, grouped into few wallet messages.

Every kind of purchase queues the same way (Stars, Premium, giveaways, in GRAM or USDT),
and they can be mixed in one group. While one message waits for its block, the next payments pile up; with max_batch
above 1 everything queued goes out in one message. Share one client so they can group.
The wallet caps a message: W5 and TG 255, V4R2 4, HighloadV2 254, HighloadV3R1 64516.
"""

import asyncio

from pyfragment import FragmentClient
from pyfragment.enums import PaymentMethod, WalletVersion

SEED = "word1 word2 ... word24"
API_KEY = "YOUR_API_KEY"  # tonconsole.com (tonapi, default) or t.me/toncenter

COOKIES = {
    "stel_token": "YOUR_STEL_TOKEN",
    "stel_ton_token": "YOUR_STEL_TON_TOKEN",
}


async def main() -> None:
    async with FragmentClient(
        seed=SEED,
        api_key=API_KEY,
        cookies=COOKIES,
        wallet_version=WalletVersion.V5R1,
        max_batch=10,
    ) as client:
        results = await asyncio.gather(
            client.purchase_stars("@username1", amount=500),
            client.purchase_stars("@username2", amount=50, payment_method=PaymentMethod.USDT_GRAM),
            client.purchase_premium("@username3", months=3),
            return_exceptions=True,
        )

    for result in results:
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
