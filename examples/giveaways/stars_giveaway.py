"""
Example: run a Telegram Stars giveaway for a channel.

amount is the Stars package the winners share: one of Fragment's packages, 500 to 1 000 000.
winners must be a whole number from 1 to amount // 100.
Channel can be "@channel", "channel", or "https://t.me/channel".
"""

import asyncio

from pyfragment import (
    AboveMaximumError,
    ChannelNotFoundError,
    ConfigurationError,
    FragmentClient,
    FragmentError,
    InvalidPackageError,
    SessionExpiredError,
    TransactionError,
    VerificationError,
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

CHANNEL = "https://t.me/channel"
WINNERS = 3  # 1 to AMOUNT // 100
AMOUNT = 1000  # Stars package shared by the winners: 500, 1000, 1500, 2500, 5000 ... 1 000 000
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
            result = await client.giveaway_stars(
                CHANNEL,
                winners=WINNERS,
                amount=AMOUNT,
                payment_method=PAYMENT_METHOD,
            )
        except ChannelNotFoundError:
            print(f"Channel {CHANNEL} was not found on fragment.com — check the username and try again.")
            return
        except InvalidPackageError:
            print(f"Fragment has no {AMOUNT} Stars package — pick one of the packages on fragment.com/stars/giveaway.")
            return
        except AboveMaximumError as e:
            print(f"Too many winners for this package: Fragment allows at most {e.maximum}.")
            return
        except ConfigurationError as e:
            print(f"Invalid argument: {e}")
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
        f"Stars giveaway created for {result.channel} — {result.winners} winner(s) × {result.amount} stars each | tx: {result.transaction_id} | confirmed: {result.confirmed}"
    )


if __name__ == "__main__":
    asyncio.run(main())
