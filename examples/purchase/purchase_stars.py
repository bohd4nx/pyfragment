"""
Example: purchase Telegram Stars for a user.

Amount must be an integer between 50 and 10 000 000.
Set show_sender=False to send anonymously.
Username can be "@username", "username", or "https://t.me/username".
"""

import asyncio

from pyfragment import (
    ConfigurationError,
    FragmentClient,
    FragmentError,
    InsufficientBalanceError,
    TransactionError,
    UserNotFoundError,
)
from pyfragment.enums import ApiProvider, PaymentMethod, WalletVersion

SEED = "word1 word2 ... word24"
API_KEY = "YOUR_API_KEY"  # tonconsole.com (tonapi, default) or t.me/toncenter

COOKIES = {
    "stel_ssid": "YOUR_STEL_SSID",
    "stel_dt": "YOUR_STEL_DT",
    "stel_token": "YOUR_STEL_TOKEN",
    "stel_ton_token": "YOUR_STEL_TON_TOKEN",
}

USERNAME = "https://t.me/username"
AMOUNT = 500  # 50–10 000 000 stars
PAYMENT_METHOD = PaymentMethod.USDT_GRAM  # PaymentMethod.GRAM or PaymentMethod.USDT_GRAM


async def main() -> None:
    async with FragmentClient(
        seed=SEED,
        api_key=API_KEY,
        cookies=COOKIES,
        wallet_version=WalletVersion.V5R1,  # or V4R2, HighloadV2, HighloadV3R1, TG (Telegram Wallet)
        api_provider=ApiProvider.TONAPI,  # or ApiProvider.TONCENTER
    ) as client:
        try:
            result = await client.purchase_stars(
                USERNAME,
                amount=AMOUNT,
                show_sender=True,
                payment_method=PAYMENT_METHOD,
            )
        except UserNotFoundError:
            print(f"User {USERNAME} was not found on fragment.com — check the username and try again.")
            return
        except ConfigurationError as e:
            print(f"Invalid argument: {e}")
            return
        except InsufficientBalanceError as e:
            print(f"Not enough funds in the wallet: {e}")
            return
        except TransactionError as e:
            print(f"Transaction failed, nothing was paid: {e}")
            return
        except FragmentError as e:
            print(f"Request failed (retryable: {e.retryable}): {e}")
            return

    print(
        f"{result.amount} Stars successfully sent to {result.username} | tx: {result.transaction_id} | confirmed: {result.confirmed}"
    )


if __name__ == "__main__":
    asyncio.run(main())
