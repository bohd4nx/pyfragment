import base64
from typing import TYPE_CHECKING, Any

from tonutils.clients import TonapiClient
from tonutils.types import NetworkGlobalID

from pyfragment.types import MIN_TON_BALANCE, WALLET_CLASSES, TransactionError, WalletError
from pyfragment.utils.decoder import clean_decode

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


def _init_ton_client(client: "FragmentClient") -> TonapiClient:
    return TonapiClient(network=NetworkGlobalID.MAINNET, api_key=client.api_key)


async def process_transaction(client: "FragmentClient", transaction_data: dict) -> str:
    """Sign and broadcast a Fragment transaction to the TON network.

    Validates the payload structure, checks the wallet balance, decodes the
    on-chain comment, and calls ``wallet.transfer``.

    Args:
        client: Authenticated :class:`FragmentClient` instance.
        transaction_data: Raw transaction dict from ``execute_transaction_request``.

    Returns:
        Normalised transaction hash string.

    Raises:
        TransactionError: If the payload is malformed or the broadcast fails.
        WalletError: If the wallet balance is too low or cannot be fetched.
    """
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
            if balance_ton < MIN_TON_BALANCE:
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
    """Fetch wallet address, public key, and state-init for the Fragment API.

    Fragment requires account info to build each transaction payload. The
    returned dict is JSON-serialised and passed as the ``account`` field in
    ``getBuy*Link`` / ``get*Link`` requests.

    Args:
        client: Authenticated :class:`FragmentClient` instance.

    Returns:
        Dict with ``address``, ``publicKey``, ``chain``, ``walletStateInit``.

    Raises:
        WalletError: If account info cannot be retrieved.
    """
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
