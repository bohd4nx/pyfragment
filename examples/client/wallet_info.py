"""
Example: fetch wallet address, state, and balance.

Cookies can be passed as a dict or as a JSON string.
wallet_version defaults to "V5R1" — change to "V4R2" for older wallets.
"""

import asyncio

from pyfragment import FragmentClient
from pyfragment.utils import get_cookies_from_browser  # noqa: F401

SEED = "word1 word2 ... word24"
API_KEY = "YOUR_TONAPI_KEY"

# Option A: extract cookies directly from your browser (no manual copy-paste needed)
# COOKIES = get_cookies_from_browser("chrome").cookies  # or "firefox", "edge", "brave", ...

# Option B: provide cookies manually
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
        wallet_version="V5R1",  # or "V4R2"
    ) as client:
        wallet = await client.get_wallet()
        print(f"Address: {wallet.address}")
        print(f"State:   {wallet.state}")
        print(f"Balance: {wallet.balance} TON")


if __name__ == "__main__":
    asyncio.run(main())
