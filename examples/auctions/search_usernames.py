"""
Example: search the Fragment marketplace for Telegram usernames.

sort is an AuctionSort: PRICE (default), PRICE_DESC, PRICE_ASC, LISTED or ENDING.
filter is an AuctionFilter: AVAILABLE (default), AUCTION, SALE or SOLD.
Fragment returns at most 500 items per query and does not page past that — narrow the query instead.
"""

import asyncio
import json

from pyfragment import AuctionFilter, AuctionSort, FragmentClient, UsernamesResult
from pyfragment.enums import ApiProvider, WalletVersion

SEED = "word1 word2 ... word24"
API_KEY = "YOUR_API_KEY"  # tonconsole.com (tonapi, default) or t.me/toncenter

# Option A: extract cookies directly from your browser (no manual copy-paste needed)
# COOKIES = get_cookies_from_browser("chrome").cookies  # or "firefox", "edge", "brave", ...

# Option B: provide cookies manually
COOKIES = {
    "stel_ssid": "YOUR_STEL_SSID",
    "stel_dt": "YOUR_STEL_DT",
    "stel_token": "YOUR_STEL_TOKEN",
    "stel_ton_token": "YOUR_STEL_TON_TOKEN",
}

QUERY = "durov"  # search term
SORT = AuctionSort.PRICE_DESC  # or omit
FILTER = AuctionFilter.AUCTION  # or omit


async def main() -> None:
    async with FragmentClient(
        seed=SEED,
        api_key=API_KEY,
        cookies=COOKIES,
        wallet_version=WalletVersion.V5R1,  # or V4R2, HighloadV2, HighloadV3R1
        api_provider=ApiProvider.TONAPI,  # or ApiProvider.TONCENTER
    ) as client:
        result: UsernamesResult = await client.search_usernames(QUERY, sort=SORT, filter=FILTER)

        print(f"Found {len(result.items)} result(s):")
        print(json.dumps(result.items, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
