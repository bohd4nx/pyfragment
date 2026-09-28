"""
Example: run a Telegram Stars giveaway for a channel.

winners must be an integer between 1 and 5.
amount (stars per winner) must be an integer between 500 and 1 000 000.
Channel can be "@channel", "channel", or "https://t.me/channel".
"""

import asyncio

from pyfragment import ChannelNotFoundError, ConfigurationError, FragmentClient, FragmentError, WalletError
from pyfragment.enums import ApiProvider, PaymentMethod, WalletVersion

SEED = "word1 word2 ... word24"
API_KEY = "YOUR_API_KEY"  # tonconsole.com (tonapi, default) or t.me/toncenter

# Option A: extract cookies directly from your browser (no manual copy-paste needed)
# COOKIES = get_cookies_from_browser("chrome").cookies  # or "firefox", "edge", "brave", ...

# Option B: provide cookies manually
COOKIES = {
    "stel_ssid": "YOUR_STEL_SSID",
    "stel_dt": "YOUR_STEL_DT",
    "stel_token": "YOUR_STEL_TOKEN",
    "stel_ton_token": "YOUR_STEL_TON_TOKEN",
}

CHANNEL = "https://t.me/channel"
WINNERS = 3  # 1–5
AMOUNT = 1000  # 500–1 000 000 stars per winner
PAYMENT_METHOD = PaymentMethod.USDT_GRAM  # PaymentMethod.GRAM or PaymentMethod.USDT_GRAM


async def main() -> None:
    async with FragmentClient(
        seed=SEED,
        api_key=API_KEY,
        cookies=COOKIES,
        wallet_version=WalletVersion.V5R1,  # or V4R2, HighloadV2, HighloadV3R1
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
        except ConfigurationError as e:
            print(f"Invalid argument: {e}")
            return
        except WalletError as e:
            print(f"Wallet problem (balance or blockchain provider): {e}")
            return
        except FragmentError as e:
            print(f"Request failed: {e}")
            return

    print(
        f"Stars giveaway created for {result.channel} — {result.winners} winner(s) × {result.amount} stars each | tx: {result.transaction_id} | confirmed: {result.confirmed}"
    )


if __name__ == "__main__":
    asyncio.run(main())
