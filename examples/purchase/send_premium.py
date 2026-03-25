"""
Example: purchase Telegram Premium for a user.

Supported durations: 3, 6, or 12 months.
Set show_sender=False to send anonymously.
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

USERNAME = "@username"
MONTHS = 3  # 3, 6 or 12


async def main() -> None:
    async with FragmentClient(seed=SEED, api_key=API_KEY, cookies=COOKIES) as client:
        try:
            result = await client.purchase_premium(USERNAME, months=MONTHS, show_sender=True)
        except UserNotFoundError:
            print(f"User {USERNAME} was not found on fragment.com — check the username and try again.")
            return
        except ConfigurationError as e:
            print(f"Invalid argument: {e}")
            return

    print(f"{result.amount} months of Premium successfully sent to {result.username} | tx: {result.transaction_id}")


if __name__ == "__main__":
    asyncio.run(main())
