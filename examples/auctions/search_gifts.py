"""
Example: search the Fragment gifts marketplace.

collection filters by gift type slug (e.g. "plushpepe", "swisswatch").
sort can be "price_desc", "price_asc", "listed", or "ending".
filter can be "", "auction", "sale", or "sold".
Use next_offset for pagination.
"""

import asyncio

from pyfragment import FragmentClient, GiftsResult

SEED = "word1 word2 ... word24"
API_KEY = "YOUR_TONAPI_KEY"
COOKIES = {
    "stel_ssid": "YOUR_STEL_SSID",
    "stel_dt": "YOUR_STEL_DT",
    "stel_token": "YOUR_STEL_TOKEN",
    "stel_ton_token": "YOUR_STEL_TON_TOKEN",
}

QUERY = ""  # search text — or omit for all
COLLECTION = "plushpepe"  # gift collection slug — or omit for all
SORT = "price_desc"  # "price_desc", "price_asc", "listed", "ending" — or omit
FILTER = ""  # "", "auction", "sale", "sold" — or omit


async def main() -> None:
    async with FragmentClient(seed=SEED, api_key=API_KEY, cookies=COOKIES) as client:
        result: GiftsResult = await client.search_gifts(
            QUERY, collection=COLLECTION, sort=SORT, filter=FILTER
        )

        print(f"Found {len(result.items)} result(s):")
        for item in result.items:
            price = f"{item['price']} TON" if item["price"] else "n/a"
            print(
                f"  {item['name']:30s}  {item['status'] or '':15s}  {price:12s}  {item['date'] or '—'}"
            )

        if result.next_offset:
            print(f"\nMore results available — next page offset: {result.next_offset}")


if __name__ == "__main__":
    asyncio.run(main())
