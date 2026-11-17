"""
Example: link the TON wallet to the Fragment account.

Run it once after connecting a wallet on fragment.com through TON Connect, before the first purchase.
It uses the stel_ton_token cookie, no extra signing is needed.
"""

import asyncio

from pyfragment import FragmentClient, FragmentError, SessionExpiredError

SEED = "word1 word2 ... word24"
API_KEY = "YOUR_API_KEY"  # tonconsole.com (tonapi, default) or t.me/toncenter

COOKIES = {
    "stel_ssid": "YOUR_STEL_SSID",
    "stel_dt": "YOUR_STEL_DT",
    "stel_token": "YOUR_STEL_TOKEN",
    "stel_ton_token": "YOUR_STEL_TON_TOKEN",
}


async def main() -> None:
    async with FragmentClient(seed=SEED, api_key=API_KEY, cookies=COOKIES) as client:
        try:
            await client.link_wallet()
        except SessionExpiredError:
            print("Fragment session expired — copy fresh cookies from fragment.com.")
            return
        except FragmentError as e:
            print(f"Request failed: {e}")
            return

    print("The wallet is linked to the Fragment account.")


if __name__ == "__main__":
    asyncio.run(main())
