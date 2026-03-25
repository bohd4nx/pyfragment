"""
Example: search the Fragment marketplace for auction listings.

type can be "usernames", "numbers", or "collectibles".
sort can be "price_desc", "price_asc", "listed", or "ending".
filter can be "", "auction", "sale", or "sold".
Use next_offset_id for pagination.
"""

import asyncio

from pyfragment import AuctionsResult, FragmentClient

SEED = "word1 word2 ... word24"
API_KEY = "YOUR_TONAPI_KEY"
COOKIES = {
    "stel_ssid": "YOUR_STEL_SSID",
    "stel_dt": "YOUR_STEL_DT",
    "stel_token": "YOUR_STEL_TOKEN",
    "stel_ton_token": "YOUR_STEL_TON_TOKEN",
}

QUERY = "durov"  # search term
TYPE = "usernames"  # "usernames", "numbers", or "collectibles" — or omit
SORT = "price_desc"  # "price_desc", "price_asc", "listed", "ending" — or omit
FILTER = "auction"  # "", "auction", "sale", "sold" — or omit


async def main() -> None:
    async with FragmentClient(seed=SEED, api_key=API_KEY, cookies=COOKIES) as client:
        result: AuctionsResult = await client.search_auctions(QUERY, type=TYPE, sort=SORT, filter=FILTER)

        print(f"Found {len(result.items)} result(s):")
        for item in result.items:
            price = f"{item['price']} TON" if item["price"] else "n/a"
            print(f"  {item['name']:20s}  {item['status'] or '':15s}  {price:10s}  {item['ends_at'] or '—'}")

        if result.next_offset_id:
            print(f"\nMore results available — next page offset: {result.next_offset_id}")


if __name__ == "__main__":
    asyncio.run(main())
