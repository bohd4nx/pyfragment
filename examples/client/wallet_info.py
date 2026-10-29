"""
Example: fetch wallet address, state, and separate GRAM (ex TON)/USDT balances.

Cookies can be passed as a dict or as a JSON string.
wallet_version defaults to "V5R1" — change to "V4R2" for older wallets, or "TG" for a Telegram Wallet
(its 12-word phrase, or 24 words after a key rotation).
mnemonic_type defaults to "ton" — pass "multichain" for the BIP-39 phrase of a multichain wallet.
Check that the printed address is the one your wallet app shows before paying anything from it.
Balances are exact Decimal values.
api_provider defaults to "tonapi" (tonconsole.com) — pass "toncenter" to use t.me/toncenter instead.
"""

import asyncio

from pyfragment import FragmentClient, FragmentError, ProviderError
from pyfragment.enums import ApiProvider, WalletVersion

SEED = "word1 word2 ... word24"
API_KEY = "YOUR_API_KEY"  # tonconsole.com (tonapi, default) or t.me/toncenter

COOKIES = {
    "stel_ssid": "YOUR_STEL_SSID",
    "stel_dt": "YOUR_STEL_DT",
    "stel_token": "YOUR_STEL_TOKEN",
    "stel_ton_token": "YOUR_STEL_TON_TOKEN",
}


async def main() -> None:
    async with FragmentClient(
        seed=SEED,
        api_key=API_KEY,
        cookies=COOKIES,
        wallet_version=WalletVersion.V5R1,  # or V4R2, HighloadV2, HighloadV3R1, TG (Telegram Wallet)
        api_provider=ApiProvider.TONAPI,  # or ApiProvider.TONCENTER
    ) as client:
        try:
            wallet = await client.get_wallet()
        except ProviderError as e:
            print(f"TON provider error — check your API key: {e}")
            return
        except FragmentError as e:
            print(f"Request failed: {e}")
            return

    print(f"Address: {wallet.address}")
    print(f"State:   {wallet.state}")
    print(f"Balance: {wallet.gram_balance} GRAM (ex TON)")
    # usdt_balance is None when the USDT lookup failed: the balance is unknown, not zero.
    print(f"Balance: {wallet.usdt_balance} USDT")


if __name__ == "__main__":
    asyncio.run(main())
