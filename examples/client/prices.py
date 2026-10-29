"""
Example: check current Stars and Premium prices on Fragment.

get_stars_price(amount) returns the GRAM cost for a given number of Stars.
get_stars_packages() returns all predefined Stars purchase options.
get_premium_packages() returns all Telegram Premium subscription durations with their prices.

No wallet interaction or purchases are made — these are read-only price checks.
"""

import asyncio

from pyfragment import ConfigurationError, FragmentClient, FragmentError, PremiumPackage, SessionExpiredError, StarsPackage
from pyfragment.enums import ApiProvider, WalletVersion

SEED = "word1 word2 ... word24"
API_KEY = "YOUR_API_KEY"  # tonconsole.com (tonapi, default) or t.me/toncenter

COOKIES = {
    "stel_ssid": "YOUR_STEL_SSID",
    "stel_dt": "YOUR_STEL_DT",
    "stel_token": "YOUR_STEL_TOKEN",
    "stel_ton_token": "YOUR_STEL_TON_TOKEN",
}

STARS_AMOUNT = 500  # how many Stars to price-check


async def main() -> None:
    async with FragmentClient(
        seed=SEED,
        api_key=API_KEY,
        cookies=COOKIES,
        wallet_version=WalletVersion.V5R1,  # or V4R2, HighloadV2, HighloadV3R1, TG (Telegram Wallet)
        api_provider=ApiProvider.TONAPI,  # or ApiProvider.TONCENTER
    ) as client:
        try:
            price = await client.get_stars_price(STARS_AMOUNT)
            packages: list[StarsPackage] = await client.get_stars_packages()
            premium_packages: list[PremiumPackage] = await client.get_premium_packages()
        except ConfigurationError as e:
            print(f"Invalid argument: {e}")
            return
        except SessionExpiredError:
            print("Fragment session expired — copy fresh cookies from fragment.com.")
            return
        except FragmentError as e:
            print(f"Request failed: {e}")
            return

    print(f"{STARS_AMOUNT} Stars = {price} GRAM\n")

    print(f"Stars packages ({len(packages)}):")
    for stars_pkg in packages:
        print(f"  {stars_pkg.stars:>9,} Stars — {stars_pkg.gram} GRAM  (~${stars_pkg.usd})")

    print(f"\nPremium packages ({len(premium_packages)}):")
    for premium_pkg in premium_packages:
        print(f"  {premium_pkg.months:>2} month(s) — {premium_pkg.gram} GRAM  (~${premium_pkg.usd})")


if __name__ == "__main__":
    asyncio.run(main())
