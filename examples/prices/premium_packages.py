"""
Example: list all Telegram Premium subscription options on Fragment.

Each package shows the duration in months, GRAM cost, and approximate USD price.
"""

import asyncio

from pyfragment import FragmentClient, FragmentError, PremiumPackage, SessionExpiredError
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
        try:
            packages: list[PremiumPackage] = await client.get_premium_packages()
        except SessionExpiredError:
            print("Fragment session expired — copy fresh cookies from fragment.com.")
            return
        except FragmentError as e:
            print(f"Request failed: {e}")
            return

    print(f"Premium packages ({len(packages)}):")
    for pkg in packages:
        print(f"  {pkg.months:>2} month(s) — {pkg.gram} GRAM  (~${pkg.usd})")


if __name__ == "__main__":
    asyncio.run(main())
