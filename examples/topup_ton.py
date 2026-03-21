"""
Example: top up a Telegram Ads account with TON.

Amount must be an integer between 1 and 1 000 000 000 TON.
Your wallet must hold at least the topup amount + ~0.056 TON for gas.
"""

import asyncio

from pyfragment import ConfigurationError, FragmentClient, UserNotFoundError, WalletError

SEED = "word1 word2 ... word24"
API_KEY = "YOUR_TONAPI_KEY"
COOKIES = {
    "stel_ssid": "YOUR_STEL_SSID",
    "stel_dt": "YOUR_STEL_DT",
    "stel_token": "YOUR_STEL_TOKEN",
    "stel_ton_token": "YOUR_STEL_TON_TOKEN",
}

USERNAME = "@username"
AMOUNT = 10  # TON, integer — 1 to 1 000 000 000


async def main() -> None:
    async with FragmentClient(seed=SEED, api_key=API_KEY, cookies=COOKIES) as client:
        try:
            result = await client.topup_ton(USERNAME, amount=AMOUNT, show_sender=True)
        except UserNotFoundError:
            print(f"User {USERNAME} was not found on fragment.com — check the username and try again.")
            return
        except WalletError as e:
            print(f"Wallet error — insufficient balance or misconfiguration: {e}")
            return
        except ConfigurationError as e:
            print(f"Invalid argument: {e}")
            return

    print(f"{result.amount} TON successfully sent to {result.username} | tx: {result.transaction_id}")


if __name__ == "__main__":
    asyncio.run(main())
