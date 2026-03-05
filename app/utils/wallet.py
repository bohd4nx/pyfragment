import base64
import json
import logging
from typing import Any

import httpx
from tonutils.clients import TonapiClient
from tonutils.types import NetworkGlobalID

from app.core import DEVICE, WALLET_CLASSES, TransactionError, WalletError, config
from app.utils.decoder import clean_decode

logger = logging.getLogger(__name__)


def initialize_ton_client() -> TonapiClient:
    return TonapiClient(network=NetworkGlobalID.MAINNET, api_key=config.API_KEY)


async def process_transaction(transaction_data: dict) -> str:
    logger.debug("transaction_data: %s", transaction_data)

    if "transaction" not in transaction_data or "messages" not in transaction_data["transaction"]:
        raise TransactionError(
            "Fragment returned an invalid transaction payload. "
            "The API response is missing expected 'transaction.messages' data."
        )

    # TODO: Investigate 406 'inbound external message rejected before smart-contract execution'.
    # This happens when the previous transaction's seqno hasn't been confirmed on-chain yet,
    # causing the wallet contract to reject the new message.
    async with initialize_ton_client() as client:
        wallet_cls = WALLET_CLASSES[config.WALLET_VERSION]
        wallet, _, _, _ = wallet_cls.from_mnemonic(client=client, mnemonic=config.SEED)

        # Check balance before broadcasting
        try:
            await wallet.refresh()
            balance_ton = wallet.balance / 1_000_000_000
            if balance_ton < 0.056:
                raise WalletError(
                    f"TON wallet balance is too low: {balance_ton:.2f} TON. "
                    "Minimum required is 0.056 TON."
                )
        except WalletError:
            raise
        except Exception as exc:
            raise WalletError(f"Wallet balance check failed: {exc}") from exc

        try:
            message = transaction_data["transaction"]["messages"][0]
            payload = clean_decode(message["payload"])

            result = await wallet.transfer(
                destination=message["address"],
                amount=int(message["amount"]),  # nanotons, not TON
                body=payload,
            )

            return result
        except (WalletError, TransactionError):
            raise
        except Exception as exc:
            raise TransactionError(f"Transaction broadcast failed: {exc}") from exc


async def get_account_info() -> dict[str, Any]:
    async with initialize_ton_client() as client:
        try:
            wallet_cls = WALLET_CLASSES[config.WALLET_VERSION]
            wallet, pub_key, _, _ = wallet_cls.from_mnemonic(client=client, mnemonic=config.SEED)
            boc = wallet.state_init.serialize().to_boc()
            return {
                "address": wallet.address.to_str(False, False),
                "publicKey": pub_key.as_hex,
                "chain": "-239",
                "walletStateInit": base64.b64encode(boc).decode(),
            }
        except Exception as exc:
            raise WalletError(f"Failed to retrieve wallet account info: {exc}") from exc


async def link_wallet(
    client: httpx.AsyncClient,
    headers: dict,
    cookies: dict,
    account: dict[str, Any],
    fragment_hash: str,
) -> bool:
    resp = await client.post(
        f"https://fragment.com/api?hash={fragment_hash}",
        headers=headers,
        cookies=cookies,
        data={
            "account": json.dumps(account),
            "device": DEVICE,
            "method": "linkWallet",
        },
    )
    result = resp.json()

    if result.get("ok"):
        return True

    if "transaction" in result:
        try:
            await process_transaction(result)
            return True
        except (TransactionError, WalletError):
            return False

    return False
