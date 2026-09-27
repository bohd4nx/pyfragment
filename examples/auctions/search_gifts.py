"""
Example: search the Fragment gifts marketplace.

collection is a gift collection slug, the last part of its URL (fragment.com/gifts/bowtie -> "bowtie").
sort is an AuctionSort: PRICE (default), PRICE_DESC, PRICE_ASC, LISTED or ENDING.
filter is an AuctionFilter: AVAILABLE (default), AUCTION, SALE or SOLD.
attr narrows a collection by trait: keys are GiftAttribute names (Model, Backdrop, Symbol).
Gifts come 60 per page; pass next_offset back as offset for the next one (Fragment stops after 1 200 items).
"""

import asyncio

from pyfragment import AuctionFilter, AuctionSort, FragmentClient, GiftAttribute
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

QUERY = ""  # search text — or omit for all
COLLECTION = "bowtie"  # gift collection slug — or omit for all
ATTR: dict[str, list[str]] = {GiftAttribute.MODEL: ["Bordeaux"]}  # trait filters — or omit
SORT = AuctionSort.PRICE_DESC  # or omit
FILTER = AuctionFilter.AVAILABLE  # or omit
MAX_ITEMS = 120  # stop paging after this many items


async def main() -> None:
    async with FragmentClient(
        seed=SEED,
        api_key=API_KEY,
        cookies=COOKIES,
        wallet_version=WalletVersion.V5R1,  # or V4R2, HighloadV2, HighloadV3R1
        api_provider=ApiProvider.TONAPI,  # or ApiProvider.TONCENTER
    ) as client:
        offset = None
        while True:
            result = await client.search_gifts(QUERY, collection=COLLECTION, sort=SORT, filter=FILTER, attr=ATTR, offset=offset)
            for gift in result.items:
                print(f"{gift['name']:<28} {gift['status'] or '-':<12} {gift['price'] or '-':>10} GRAM")

            offset = result.next_offset
            if offset is None or offset >= MAX_ITEMS:
                break


if __name__ == "__main__":
    asyncio.run(main())
