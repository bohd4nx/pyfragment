"""
Example: manage an anonymous Telegram number — read login code and terminate sessions.

Use get_login_code() to fetch the current pending login code for your number.
Use toggle_login_codes() to enable or disable receiving codes.
Use terminate_sessions() to forcefully end all active Telegram sessions.
"""

import asyncio

from pyfragment import AnonymousNumberError, FragmentClient, FragmentError, SessionExpiredError
from pyfragment.enums import ApiProvider, WalletVersion

SEED = "word1 word2 ... word24"
API_KEY = "YOUR_API_KEY"  # tonconsole.com (tonapi, default) or t.me/toncenter

COOKIES = {
    "stel_ssid": "YOUR_STEL_SSID",
    "stel_dt": "YOUR_STEL_DT",
    "stel_token": "YOUR_STEL_TOKEN",
    "stel_ton_token": "YOUR_STEL_TON_TOKEN",
}

NUMBER = "+88888888888"


async def main() -> None:
    async with FragmentClient(
        seed=SEED,
        api_key=API_KEY,
        cookies=COOKIES,
        wallet_version=WalletVersion.V5R1,  # or V4R2, HighloadV2, HighloadV3R1, TG (Telegram Wallet)
        api_provider=ApiProvider.TONAPI,  # or ApiProvider.TONCENTER
    ) as client:
        try:
            result = await client.get_login_code(NUMBER)
        except AnonymousNumberError as e:
            print(f"Could not fetch login code: {e}")
            return
        except SessionExpiredError:
            print("Fragment session expired — copy fresh cookies from fragment.com.")
            return
        except FragmentError as e:
            print(f"Request failed: {e}")
            return

        if result.code:
            print(f"Login code for {result.number}: {result.code} ({result.active_sessions} active session(s))")
        else:
            print(f"No pending login code for {result.number} ({result.active_sessions} active session(s))")

        try:
            terminated = await client.terminate_sessions(NUMBER)
        except AnonymousNumberError as e:
            print(f"Could not terminate sessions: {e}")
            return
        except SessionExpiredError:
            print("Fragment session expired — copy fresh cookies from fragment.com.")
            return
        except FragmentError as e:
            print(f"Request failed: {e}")
            return

        print(f"Sessions terminated for {terminated.number}" + (f": {terminated.message}" if terminated.message else ""))


if __name__ == "__main__":
    asyncio.run(main())
