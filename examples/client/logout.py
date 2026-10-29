"""
Example: end the Fragment session and disconnect the linked TON wallet.

logout() invalidates session cookies server-side — you will need fresh cookies afterwards.
disconnect_wallet() unlinks the TON wallet from Fragment without ending the session.
"""

import asyncio

from pyfragment import FragmentClient, FragmentError, SessionExpiredError
from pyfragment.enums import ApiProvider, WalletVersion

SEED = "word1 word2 ... word24"
API_KEY = "YOUR_API_KEY"  # tonconsole.com (tonapi, default) or t.me/toncenter

COOKIES = {
    "stel_ssid": "YOUR_STEL_SSID",
    "stel_dt": "YOUR_STEL_DT",
    "stel_token": "YOUR_STEL_TOKEN",
    "stel_ton_token": "YOUR_STEL_TON_TOKEN",
}

# Set to True to also disconnect the linked TON wallet before logging out.
DISCONNECT_WALLET_FIRST = False


async def main() -> None:
    async with FragmentClient(
        seed=SEED,
        api_key=API_KEY,
        cookies=COOKIES,
        wallet_version=WalletVersion.V5R1,  # or V4R2, HighloadV2, HighloadV3R1, TG (Telegram Wallet)
        api_provider=ApiProvider.TONAPI,  # or ApiProvider.TONCENTER
    ) as client:
        try:
            if DISCONNECT_WALLET_FIRST:
                await client.disconnect_wallet()
                print("TON wallet disconnected from Fragment.")

            await client.logout()
        except SessionExpiredError:
            print("Session was already expired.")
            return
        except FragmentError as e:
            print(f"Request failed: {e}")
            return

    print("Logged out of Fragment. Cookies are no longer valid.")


if __name__ == "__main__":
    asyncio.run(main())
