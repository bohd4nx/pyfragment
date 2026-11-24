"""
Example: never lose track of a payment.

on_transfer_prepared receives every signed transfer BEFORE it is sent. Save it: if the process dies before
purchase_stars() returns, msg_hash and comment tell you on-chain whether the payment went out. If the callback raises,
that payment is not sent. confirm_timeout is how long to wait for Fragment's own confirmation. confirmed=False usually means
Fragment is just slow, but an underfunded wallet looks the same (its transfer fails on-chain), so neither retry nor
assume it was paid: look the transfer up by transaction_id first. retryable=True on an error means nothing was paid.
"""

import asyncio

from pyfragment import FragmentClient, FragmentError, TransferIntent

SEED = "word1 word2 ... word24"
API_KEY = "YOUR_API_KEY"  # tonconsole.com (tonapi, default) or t.me/toncenter

COOKIES = {
    "stel_token": "YOUR_STEL_TOKEN",
    "stel_ton_token": "YOUR_STEL_TON_TOKEN",
}

payments: dict[str, TransferIntent] = {}  # use a database in real code


async def save(intent: TransferIntent) -> None:
    payments[intent.req_id or intent.msg_hash] = intent


async def main() -> None:
    async with FragmentClient(
        seed=SEED,
        api_key=API_KEY,
        cookies=COOKIES,
        on_transfer_prepared=save,
        confirm_timeout=30,
    ) as client:
        try:
            result = await client.purchase_stars("@username", amount=500)
        except FragmentError as e:
            print(f"Failed: {e}")
            print("Safe to start the purchase again." if e.retryable else "Check the wallet before trying again.")
            return

    print(f"tx {result.transaction_id} | confirmed: {result.confirmed}")
    if not result.confirmed:
        print("Fragment has not confirmed yet. Look the transfer up on-chain before buying again: it may be unfunded.")


if __name__ == "__main__":
    asyncio.run(main())
