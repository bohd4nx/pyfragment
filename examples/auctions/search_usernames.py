"""
Example: search the Fragment marketplace for Telegram usernames.

sort can be "price_desc", "price_asc", "listed", or "ending".
filter can be "", "auction", "sale", or "sold".
Use next_offset_id for pagination.
"""

import asyncio

from pyfragment import FragmentClient, UsernamesResult

SEED = "word1 word2 ... word24"
API_KEY = "YOUR_TONAPI_KEY"
COOKIES = {
    "stel_ssid": "YOUR_STEL_SSID",
    "stel_dt": "YOUR_STEL_DT",
    "stel_token": "YOUR_STEL_TOKEN",
    "stel_ton_token": "YOUR_STEL_TON_TOKEN",
}

QUERY = "durov"  # search term
SORT = "price_desc"  # "price_desc", "price_asc", "listed", "ending" — or omit
FILTER = "auction"  # "", "auction", "sale", "sold" — or omit


async def main() -> None:
    async with FragmentClient(seed=SEED, api_key=API_KEY, cookies=COOKIES) as client:
        result: UsernamesResult = await client.search_usernames(
            QUERY, sort=SORT, filter=FILTER
        )

        print(f"Found {len(result.items)} result(s):")
        for item in result.items:
            price = f"{item['price']} TON" if item["price"] else "n/a"
            print(
                f"  {item['name']:20s}  {item['status'] or '':15s}  {price:10s}  {item['date'] or '—'}"
            )

        if result.next_offset_id:
            print(
                f"\nMore results available — next page offset: {result.next_offset_id}"
            )


if __name__ == "__main__":
    asyncio.run(main())
