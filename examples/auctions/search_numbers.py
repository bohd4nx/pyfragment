"""
Example: search the Fragment marketplace for anonymous Telegram numbers.

sort can be "price_desc", "price_asc", "listed", or "ending".
filter can be "", "auction", "sale", or "sold".
Use next_offset_id for pagination.
"""

import asyncio
import json

from pyfragment import FragmentClient, NumbersResult

SEED = "word1 word2 ... word24"
API_KEY = "YOUR_TONAPI_KEY"
COOKIES = {
    "stel_ssid": "YOUR_STEL_SSID",
    "stel_dt": "YOUR_STEL_DT",
    "stel_token": "YOUR_STEL_TOKEN",
    "stel_ton_token": "YOUR_STEL_TON_TOKEN",
}

QUERY = "888"  # search term — or omit for all
SORT = "price_asc"  # "price_desc", "price_asc", "listed", "ending" — or omit
FILTER = ""  # "", "auction", "sale", "sold" — or omit


async def main() -> None:
    async with FragmentClient(seed=SEED, api_key=API_KEY, cookies=COOKIES) as client:
        result: NumbersResult = await client.search_numbers(QUERY, sort=SORT, filter=FILTER)

        print(f"Found {len(result.items)} result(s):")
        print(json.dumps(result.items, indent=2))

        if result.next_offset_id:
            print(f"\nMore results available — next page offset: {result.next_offset_id}")


if __name__ == "__main__":
    asyncio.run(main())
