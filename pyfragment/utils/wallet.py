import asyncio
import base64
from typing import TYPE_CHECKING, Any

from tonutils.clients import TonapiClient
from tonutils.exceptions import ProviderResponseError
from tonutils.types import NetworkGlobalID

from pyfragment.types import MIN_TON_BALANCE, WALLET_CLASSES, TransactionError, WalletError
from pyfragment.types.results import WalletInfo
from pyfragment.utils.decoder import clean_decode

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


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

    message = transaction_data["transaction"]["messages"][0]
    amount_ton = int(message["amount"]) / 1_000_000_000

    # TODO: Investigate 406 'inbound external message rejected before smart-contract execution'.
    # This happens when the previous transaction's seqno hasn't been confirmed on-chain yet,
    # causing the wallet contract to reject the new message.
    async with TonapiClient(network=NetworkGlobalID.MAINNET, api_key=client.api_key) as ton:
        wallet_cls = WALLET_CLASSES[client.wallet_version]
        wallet, _, _, _ = wallet_cls.from_mnemonic(client=ton, mnemonic=client.seed)

        # Check balance covers transaction amount + gas reserve
        try:
            await wallet.refresh()
            balance_ton = wallet.balance / 1_000_000_000
            required = amount_ton + MIN_TON_BALANCE
            if balance_ton < required:
                raise WalletError(WalletError.LOW_BALANCE.format(balance=balance_ton, required=required))
        except WalletError:
            raise
        except Exception as exc:
            raise WalletError(WalletError.BALANCE_CHECK_FAILED.format(exc=exc)) from exc

        try:
            payload = clean_decode(message["payload"])

            for attempt in range(2):
                try:
                    result = await wallet.transfer(
                        destination=message["address"],
                        amount=int(message["amount"]),  # nanotons, not TON
                        body=payload,
                    )
                    return result.normalized_hash
                except ProviderResponseError as exc:
                    if exc.code == 429 and attempt == 0:
                        await asyncio.sleep(1)
                        continue
                    raise
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
    async with TonapiClient(network=NetworkGlobalID.MAINNET, api_key=client.api_key) as ton:
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


async def get_wallet_info(client: "FragmentClient") -> "WalletInfo":
    """Return the address, state and balance of the TON wallet.

    Args:
        client: Authenticated :class:`FragmentClient` instance.

    Returns:
        :class:`WalletInfo` with ``address``, ``state``, and ``balance`` in TON.

    Raises:
        WalletError: If the wallet state cannot be fetched.
    """
    async with TonapiClient(network=NetworkGlobalID.MAINNET, api_key=client.api_key) as ton:
        try:
            wallet_cls = WALLET_CLASSES[client.wallet_version]
            wallet, _, _, _ = wallet_cls.from_mnemonic(client=ton, mnemonic=client.seed)
            await wallet.refresh()
            return WalletInfo(
                address=wallet.address.to_str(is_user_friendly=True, is_bounceable=False),
                state=wallet.state.value,
                balance=round(wallet.balance / 1_000_000_000, 4),
            )
        except Exception as exc:
            raise WalletError(WalletError.WALLET_INFO_FAILED.format(exc=exc)) from exc
