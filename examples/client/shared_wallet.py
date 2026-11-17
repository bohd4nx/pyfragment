"""
Example: several processes buying from one wallet.

A wallet lands one message per block and a node rejects a seqno that is ahead of the chain, so processes sharing a
seed have to take turns signing. A TransferCoordinator is that turn: a lock plus the seqno of the last sent message.
This one is backed by Redis (pip install redis). Combine it with max_batch to send many payments in one message.
"""

import asyncio
from contextlib import AbstractAsyncContextManager
from typing import cast

from redis.asyncio import Redis

from pyfragment import FragmentClient

SEED = "word1 word2 ... word24"
API_KEY = "YOUR_API_KEY"  # tonconsole.com (tonapi, default) or t.me/toncenter

COOKIES = {
    "stel_ssid": "YOUR_STEL_SSID",
    "stel_dt": "YOUR_STEL_DT",
    "stel_token": "YOUR_STEL_TOKEN",
    "stel_ton_token": "YOUR_STEL_TON_TOKEN",
}

# One coordinator per wallet: its keys carry no wallet address, so use other keys for another wallet.
redis = Redis.from_url("redis://localhost:6379/0")


class RedisCoordinator:
    def lock(self) -> AbstractAsyncContextManager[object]:
        return cast(AbstractAsyncContextManager[object], redis.lock("wallet-lock", timeout=120, blocking_timeout=300))

    async def load_pending(self) -> tuple[int, float] | None:
        raw = await redis.get("wallet-pending")
        if raw is None:
            return None
        seqno, valid_until = raw.decode().split(":")
        return int(seqno), float(valid_until)

    async def save_pending(self, seqno: int, valid_until: float) -> None:
        await redis.set("wallet-pending", f"{seqno}:{valid_until}", ex=120)


async def main() -> None:
    async with FragmentClient(
        seed=SEED,
        api_key=API_KEY,
        cookies=COOKIES,
        transfer_coordinator=RedisCoordinator(),
        max_batch=50,
    ) as client:
        results = await asyncio.gather(
            *(client.purchase_stars(f"user{i}", amount=50) for i in range(10)),
            return_exceptions=True,
        )

    for result in results:
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
