"""
Example: get the current GRAM price for a given number of Stars.

Returns the exact GRAM cost as a Decimal for the specified Stars amount.
Amount must be an integer between 50 and 10 000 000.
"""

import asyncio

from pyfragment import ConfigurationError, FragmentClient, FragmentError, SessionExpiredError
from pyfragment.enums import ApiProvider, WalletVersion

SEED = "word1 word2 ... word24"
API_KEY = "YOUR_API_KEY"  # tonconsole.com (tonapi, default) or t.me/toncenter

COOKIES = {
    "stel_ssid": "YOUR_STEL_SSID",
    "stel_dt": "YOUR_STEL_DT",
    "stel_token": "YOUR_STEL_TOKEN",
    "stel_ton_token": "YOUR_STEL_TON_TOKEN",
}

AMOUNT = 500  # Stars to price-check (50–10 000 000)


async def main() -> None:
    async with FragmentClient(
        seed=SEED,
        api_key=API_KEY,
        cookies=COOKIES,
        wallet_version=WalletVersion.V5R1,  # or V4R2, HighloadV2, HighloadV3R1, TG (Telegram Wallet)
        api_provider=ApiProvider.TONAPI,  # or ApiProvider.TONCENTER
    ) as client:
        try:
            price = await client.get_stars_price(AMOUNT)
        except ConfigurationError as e:
            print(f"Invalid argument: {e}")
            return
        except SessionExpiredError:
            print("Fragment session expired — copy fresh cookies from fragment.com.")
            return
        except FragmentError as e:
            print(f"Request failed: {e}")
            return

    print(f"{AMOUNT} Stars = {price} GRAM")


if __name__ == "__main__":
    asyncio.run(main())
