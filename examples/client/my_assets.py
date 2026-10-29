"""
Example: list your own Fragment assets — usernames, anonymous numbers, and gifts.

get_my_usernames() returns all Telegram usernames in your Fragment account.
get_my_numbers() returns all anonymous Telegram numbers you own.
get_my_gifts() returns all gifts in your Fragment collection.

These require a valid Fragment session (stel_ssid, stel_token, stel_dt cookies).
"""

import asyncio

from pyfragment import FragmentClient, MyGiftsResult, MyNumbersResult, MyUsernamesResult
from pyfragment.enums import ApiProvider, WalletVersion

SEED = "word1 word2 ... word24"
API_KEY = "YOUR_API_KEY"  # tonconsole.com (tonapi, default) or t.me/toncenter

COOKIES = {
    "stel_ssid": "YOUR_STEL_SSID",
    "stel_dt": "YOUR_STEL_DT",
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
        usernames: MyUsernamesResult = await client.get_my_usernames()
        print(f"Usernames ({len(usernames.items)}):")
        for item in usernames.items:
            print(f"  @{item['name']}")

        numbers: MyNumbersResult = await client.get_my_numbers()
        print(f"\nAnonymous numbers ({len(numbers.items)}):")
        for item in numbers.items:
            print(f"  {item['name']}")

        gifts: MyGiftsResult = await client.get_my_gifts()
        print(f"\nGifts ({len(gifts.items)}):")
        for item in gifts.items:
            print(f"  {item['name']}")


if __name__ == "__main__":
    asyncio.run(main())
