"""
Example: recharge your own Telegram Ads account with GRAM (ex TON).

Amount must be an integer between 1 and 1 000 000 000 GRAM (ex TON).
Your wallet must satisfy the current minimum GRAM (ex TON) threshold and transaction cost.
"""

import asyncio

from pyfragment import (
    AdsRechargeResult,
    ConfigurationError,
    FragmentClient,
    FragmentError,
    InsufficientBalanceError,
    SessionExpiredError,
    TransactionError,
    VerificationError,
)
from pyfragment.enums import ApiProvider, WalletVersion

SEED = "word1 word2 ... word24"
API_KEY = "YOUR_API_KEY"  # tonconsole.com (tonapi, default) or t.me/toncenter

COOKIES = {
    "stel_ssid": "YOUR_STEL_SSID",
    "stel_dt": "YOUR_STEL_DT",
    "stel_token": "YOUR_STEL_TOKEN",
    "stel_ton_token": "YOUR_STEL_TON_TOKEN",
}

ACCOUNT = "@mychannel"  # channel or bot username linked to your Telegram Ads account
AMOUNT = 10  # 1–1 000 000 000 GRAM (ex TON)


async def main() -> None:
    async with FragmentClient(
        seed=SEED,
        api_key=API_KEY,
        cookies=COOKIES,
        wallet_version=WalletVersion.V5R1,  # or V4R2, HighloadV2, HighloadV3R1, TG (Telegram Wallet)
        api_provider=ApiProvider.TONAPI,  # or ApiProvider.TONCENTER
    ) as client:
        try:
            result: AdsRechargeResult = await client.recharge_ads(ACCOUNT, amount=AMOUNT)
        except ConfigurationError as e:
            print(f"Invalid argument: {e}")
            return
        except InsufficientBalanceError as e:
            print(f"Not enough funds in the wallet: {e}")
            return
        except VerificationError:
            print("Fragment requires identity verification for this purchase.")
            return
        except SessionExpiredError:
            print("Fragment session expired — copy fresh cookies from fragment.com.")
            return
        except TransactionError as e:
            print(f"Transaction failed, nothing was paid: {e}")
            return
        except FragmentError as e:
            print(f"Request failed: {e}")
            return

    print(
        f"{result.amount} GRAM (ex TON) recharged to Ads account {ACCOUNT} | tx: {result.transaction_id} | confirmed: {result.confirmed}"
    )


if __name__ == "__main__":
    asyncio.run(main())
