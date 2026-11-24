"""
Example: list the Stars and Premium gifts the account has bought.

Read-only: it opens fragment.com/stars/history and fragment.com/premium/history and buys nothing.
Fragment lists at most 1000 purchases per order, newest first by default.
"""

import asyncio

from pyfragment import FragmentClient, FragmentError, SessionExpiredError
from pyfragment.enums import ApiProvider, WalletVersion

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
        wallet_version=WalletVersion.V5R1,  # or V4R2, HighloadV2, HighloadV3R1, TG (Telegram Wallet)
        api_provider=ApiProvider.TONAPI,  # or ApiProvider.TONCENTER
    ) as client:
        try:
            stars = await client.get_stars_history()
            premium = await client.get_premium_history()
        except SessionExpiredError:
            print("Fragment session expired — copy fresh cookies from fragment.com.")
            return
        except FragmentError as e:
            print(f"Request failed: {e}")
            return

    print(f"Stars purchases ({len(stars)}), {sum(e.stars for e in stars):,} Stars in total:")
    for purchase in stars[:5]:
        print(f"  {purchase.date:%Y-%m-%d %H:%M}  {purchase.name:<20} {purchase.stars:>7,} Stars — {purchase.gram} GRAM")

    print(f"Premium gifts ({len(premium)}):")
    for gift in premium[:5]:
        print(f"  {gift.date:%Y-%m-%d %H:%M}  {gift.name:<20} {gift.months:>2} months — {gift.gram} GRAM")


if __name__ == "__main__":
    asyncio.run(main())
