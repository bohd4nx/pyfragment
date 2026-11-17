"""
Example: check that Fragment can deliver to a user before buying anything.

check_stars_recipient() and check_premium_recipient() only look the user up: nothing is paid.
Premium also fails for a user who already has an active subscription.
"""

import asyncio

from pyfragment import AlreadySubscribedError, FragmentClient, FragmentError, UserNotFoundError

SEED = "word1 word2 ... word24"
API_KEY = "YOUR_API_KEY"  # tonconsole.com (tonapi, default) or t.me/toncenter

COOKIES = {
    "stel_ssid": "YOUR_STEL_SSID",
    "stel_dt": "YOUR_STEL_DT",
    "stel_token": "YOUR_STEL_TOKEN",
    "stel_ton_token": "YOUR_STEL_TON_TOKEN",
}

USERNAME = "@username"


async def main() -> None:
    async with FragmentClient(seed=SEED, api_key=API_KEY, cookies=COOKIES) as client:
        try:
            stars_recipient = await client.check_stars_recipient(USERNAME)
            print(f"Stars can be sent to {stars_recipient.username} ({stars_recipient.name})")
        except UserNotFoundError:
            print(f"{USERNAME} was not found on fragment.com.")
            return
        except FragmentError as e:
            print(f"Request failed: {e}")
            return

        try:
            await client.check_premium_recipient(USERNAME, months=3)
            print(f"Premium can be gifted to {USERNAME}")
        except AlreadySubscribedError:
            print(f"{USERNAME} already has Telegram Premium.")
        except FragmentError as e:
            print(f"Request failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
