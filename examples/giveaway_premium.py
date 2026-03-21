"""
Example: run a Telegram Premium giveaway for a channel.

winners must be an integer between 1 and 24 000.
months (Premium duration per winner) must be 3, 6, or 12.
"""

import asyncio

from pyfragment import ConfigurationError, FragmentClient, UserNotFoundError

SEED = "word1 word2 ... word24"
API_KEY = "YOUR_TONAPI_KEY"
COOKIES = {
    "stel_ssid": "YOUR_STEL_SSID",
    "stel_dt": "YOUR_STEL_DT",
    "stel_token": "YOUR_STEL_TOKEN",
    "stel_ton_token": "YOUR_STEL_TON_TOKEN",
}

CHANNEL = "@channel"
WINNERS = 10  # 1–24 000
MONTHS = 3  # 3, 6 or 12


async def main() -> None:
    async with FragmentClient(seed=SEED, api_key=API_KEY, cookies=COOKIES) as client:
        try:
            result = await client.giveaway_premium(CHANNEL, winners=WINNERS, months=MONTHS)
        except UserNotFoundError:
            print(f"Channel {CHANNEL} was not found on fragment.com — check the username and try again.")
            return
        except ConfigurationError as e:
            print(f"Invalid argument: {e}")
            return

    print(
        f"Premium giveaway created for {result.channel} — {result.winners} winners × {result.amount} months | tx: {result.transaction_id}"
    )


if __name__ == "__main__":
    asyncio.run(main())
