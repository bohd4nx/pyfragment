import base64
from typing import TYPE_CHECKING, Any

from tonutils.clients import TonapiClient
from tonutils.types import NetworkGlobalID

from fragmentapi.types import WALLET_CLASSES, TransactionError, WalletError
from fragmentapi.utils.decoder import clean_decode

if TYPE_CHECKING:
    from fragmentapi.client import FragmentClient


def _init_ton_client(client: "FragmentClient") -> TonapiClient:
    return TonapiClient(network=NetworkGlobalID.MAINNET, api_key=client.api_key)


async def process_transaction(client: "FragmentClient", transaction_data: dict) -> str:
    if "transaction" not in transaction_data or "messages" not in transaction_data["transaction"]:
        raise TransactionError(TransactionError.INVALID_PAYLOAD)

    # TODO: Investigate 406 'inbound external message rejected before smart-contract execution'.
    # This happens when the previous transaction's seqno hasn't been confirmed on-chain yet,
    # causing the wallet contract to reject the new message.
    async with _init_ton_client(client) as ton:
        wallet_cls = WALLET_CLASSES[client.wallet_version]
        wallet, _, _, _ = wallet_cls.from_mnemonic(client=ton, mnemonic=client.seed)

        # Check balance before broadcasting
        try:
            await wallet.refresh()
            balance_ton = wallet.balance / 1_000_000_000
            if balance_ton < 0.056:
                raise WalletError(WalletError.LOW_BALANCE.format(balance=balance_ton))
        except WalletError:
            raise
        except Exception as exc:
            raise WalletError(WalletError.BALANCE_CHECK_FAILED.format(exc=exc)) from exc

        try:
            message = transaction_data["transaction"]["messages"][0]
            payload = clean_decode(message["payload"])

            result = await wallet.transfer(
                destination=message["address"],
                amount=int(message["amount"]),  # nanotons, not TON
                body=payload,
            )
            return result.normalized_hash
        except (WalletError, TransactionError):
            raise
        except Exception as exc:
            raise TransactionError(TransactionError.BROADCAST_FAILED.format(exc=exc)) from exc


async def get_account_info(client: "FragmentClient") -> dict[str, Any]:
    async with _init_ton_client(client) as ton:
        try:
            wallet_cls = WALLET_CLASSES[client.wallet_version]
            wallet, pub_key, _, _ = wallet_cls.from_mnemonic(client=ton, mnemonic=client.seed)
            boc = wallet.state_init.serialize().to_boc()
            return {
                "address": wallet.address.to_str(False, False),
                "publicKey": pub_key.as_hex,
                "chain": "-239",
                "walletStateInit": base64.b64encode(boc).decode(),
            }
        except Exception as exc:
            raise WalletError(WalletError.ACCOUNT_INFO_FAILED.format(exc=exc)) from exc
