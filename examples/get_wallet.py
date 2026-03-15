"""
Example: initializing FragmentClient.

Cookies can be passed as a dict or as a JSON string.
wallet_version defaults to "V5R1" — change to "V4R2" for older wallets.
"""

import asyncio

from pyfragment import FragmentClient

SEED = "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12 word13 word14 word15 word16 word17 word18 word19 word20 word21 word22 word23 word24"
API_KEY = "YOUR_TONAPI_KEY"
COOKIES = {
    "stel_ssid": "YOUR_STEL_SSID",
    "stel_dt": "YOUR_STEL_DT",
    "stel_token": "YOUR_STEL_TOKEN",
    "stel_ton_token": "YOUR_STEL_TON_TOKEN",
}


async def main() -> None:
    client = FragmentClient(
        seed=SEED,
        api_key=API_KEY,
        cookies=COOKIES,
        wallet_version="V5R1",  # or "V4R2"
    )

    wallet = await client.get_wallet()

    print("FragmentClient initialized")
    print("   %-16s %s" % ("Wallet version:", client.wallet_version))
    print("   %-16s %s" % ("Address:", wallet.address))
    print("   %-16s %s" % ("State:", wallet.state))
    print("   %-16s %s TON" % ("Balance:", wallet.balance))


if __name__ == "__main__":
    asyncio.run(main())
