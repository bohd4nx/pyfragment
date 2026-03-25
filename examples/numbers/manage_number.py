"""
Example: manage an anonymous Telegram number — read login code and terminate sessions.

Use get_login_code() to fetch the current pending login code for your number.
Use toggle_login_codes() to enable or disable receiving codes.
Use terminate_sessions() to forcefully end all active Telegram sessions.
"""

import asyncio

from pyfragment import AnonymousNumberError, FragmentClient

SEED = "word1 word2 ... word24"
API_KEY = "YOUR_TONAPI_KEY"
COOKIES = {
    "stel_ssid": "YOUR_STEL_SSID",
    "stel_dt": "YOUR_STEL_DT",
    "stel_token": "YOUR_STEL_TOKEN",
    "stel_ton_token": "YOUR_STEL_TON_TOKEN",
}

NUMBER = "+88888888888"


async def main() -> None:
    async with FragmentClient(seed=SEED, api_key=API_KEY, cookies=COOKIES) as client:
        # Fetch the latest login code
        result = await client.get_login_code(NUMBER)
        if result.code:
            print(f"Login code for {result.number}: {result.code} ({result.active_sessions} active session(s))")
        else:
            print(f"No pending login code for {result.number} ({result.active_sessions} active session(s))")

        # Terminate all active sessions
        try:
            terminated = await client.terminate_sessions(NUMBER)
            print(f"Sessions terminated for {terminated.number}" + (f": {terminated.message}" if terminated.message else ""))
        except AnonymousNumberError as e:
            print(f"Could not terminate sessions: {e}")


if __name__ == "__main__":
    asyncio.run(main())
