"""
Example: search the Fragment marketplace for anonymous Telegram numbers.

sort is an AuctionSort: PRICE (default), PRICE_DESC, PRICE_ASC, LISTED or ENDING.
filter is an AuctionFilter: AVAILABLE (default), AUCTION, SALE or SOLD.
Fragment returns at most 500 items per query and does not page past that — narrow the query instead.
"""

import asyncio
import json

from pyfragment import AuctionFilter, AuctionSort, FragmentClient, FragmentError, NumbersResult, SessionExpiredError
from pyfragment.enums import ApiProvider, WalletVersion

SEED = "word1 word2 ... word24"
API_KEY = "YOUR_API_KEY"  # tonconsole.com (tonapi, default) or t.me/toncenter

COOKIES = {
    "stel_ssid": "YOUR_STEL_SSID",
    "stel_dt": "YOUR_STEL_DT",
    "stel_token": "YOUR_STEL_TOKEN",
    "stel_ton_token": "YOUR_STEL_TON_TOKEN",
}

QUERY = "888"  # search term — or omit for all
SORT = AuctionSort.PRICE_ASC  # or omit
FILTER = AuctionFilter.AVAILABLE  # or omit


async def main() -> None:
    async with FragmentClient(
        seed=SEED,
        api_key=API_KEY,
        cookies=COOKIES,
        wallet_version=WalletVersion.V5R1,  # or V4R2, HighloadV2, HighloadV3R1, TG (Telegram Wallet)
        api_provider=ApiProvider.TONAPI,  # or ApiProvider.TONCENTER
    ) as client:
        try:
            result: NumbersResult = await client.search_numbers(QUERY, sort=SORT, filter=FILTER)
        except SessionExpiredError:
            print("Fragment session expired — copy fresh cookies from fragment.com.")
            return
        except FragmentError as e:
            print(f"Request failed: {e}")
            return

    print(f"Found {len(result.items)} result(s):")
    print(json.dumps(result.items, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
