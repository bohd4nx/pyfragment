"""
Example: run a Telegram Stars giveaway for a channel.

winners must be an integer between 1 and 5.
amount (stars per winner) must be an integer between 500 and 1 000 000.
"""

import asyncio

from pyfragment import ConfigurationError, FragmentClient, UserNotFoundError
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

CHANNEL = "@channel"
WINNERS = 3  # 1–5
AMOUNT = 1000  # 500–1 000 000 stars per winner


async def main() -> None:
    async with FragmentClient(seed=SEED, api_key=API_KEY, cookies=COOKIES) as client:
        try:
            result = await client.giveaway_stars(CHANNEL, winners=WINNERS, amount=AMOUNT)
        except UserNotFoundError:
            print(f"Channel {CHANNEL} was not found on fragment.com — check the username and try again.")
            return
        except ConfigurationError as e:
            print(f"Invalid argument: {e}")
            return

    print(
        f"Stars giveaway created for {result.channel} — {result.winners} winner(s) × {result.amount} stars each | tx: {result.transaction_id}"
    )


if __name__ == "__main__":
    asyncio.run(main())
