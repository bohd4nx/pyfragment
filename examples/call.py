"""
Example: send a raw request to any Fragment API method.

Use client.call() when you need to access a method that is not yet
wrapped by the library, or to inspect raw API responses directly.

page_url must match the Fragment page the method belongs to — Fragment
requires a hash derived from each specific page.
"""

import asyncio

from pyfragment import FragmentClient

SEED = "word1 word2 ... word24"
API_KEY = "YOUR_TONAPI_KEY"
COOKIES = {
    "stel_ssid": "YOUR_STEL_SSID",
    "stel_dt": "YOUR_STEL_DT",
    "stel_token": "YOUR_STEL_TOKEN",
    "stel_ton_token": "YOUR_STEL_TON_TOKEN",
}

METHOD = "anyFragmentMethod"  # replace with the actual method name
DATA = {"key": "value"}  # replace with the actual request payload
PAGE_URL = "https://fragment.com/stars/buy"  # replace with the matching Fragment page


async def main() -> None:
    async with FragmentClient(seed=SEED, api_key=API_KEY, cookies=COOKIES) as client:
        result = await client.call(METHOD, DATA, page_url=PAGE_URL)
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
