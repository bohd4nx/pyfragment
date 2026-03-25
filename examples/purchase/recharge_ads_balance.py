"""
Example: recharge your own Telegram Ads account with TON.

Amount must be an integer between 1 and 1 000 000 000 TON.
Your wallet must hold at least the recharge amount + ~0.056 TON for gas.
"""

import asyncio

from pyfragment import (
    AdsRechargeResult,
    ConfigurationError,
    FragmentClient,
    WalletError,
)

SEED = "word1 word2 ... word24"
API_KEY = "YOUR_TONAPI_KEY"
COOKIES = {
    "stel_ssid": "YOUR_STEL_SSID",
    "stel_dt": "YOUR_STEL_DT",
    "stel_token": "YOUR_STEL_TOKEN",
    "stel_ton_token": "YOUR_STEL_TON_TOKEN",
}

ACCOUNT = "@mychannel"  # channel or bot username linked to your Telegram Ads account
AMOUNT = 10  # 1–1 000 000 000 TON


async def main() -> None:
    async with FragmentClient(seed=SEED, api_key=API_KEY, cookies=COOKIES) as client:
        try:
            result: AdsRechargeResult = await client.recharge_ads(ACCOUNT, amount=AMOUNT)
        except WalletError as e:
            print(f"Wallet error — insufficient balance or misconfiguration: {e}")
            return
        except ConfigurationError as e:
            print(f"Invalid argument: {e}")
            return

    print(f"{result.amount} TON recharged to Ads account {ACCOUNT} | tx: {result.transaction_id}")


if __name__ == "__main__":
    asyncio.run(main())
