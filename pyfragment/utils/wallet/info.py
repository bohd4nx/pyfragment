from __future__ import annotations

import base64
from typing import TYPE_CHECKING, Any

from ton_core import NetworkGlobalID
from tonutils.clients import TonapiClient

from pyfragment.types import WalletError, WalletInfo
from pyfragment.types.constants import WALLET_CLASSES
from pyfragment.utils.wallet.balance import get_usdt_balance

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


async def get_account_info(client: FragmentClient) -> dict[str, Any]:
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


async def get_wallet_info(client: FragmentClient) -> WalletInfo:
    """Return the address, state and balance of the TON wallet.

    Args:
        client: Authenticated :class:`FragmentClient` instance.

    Returns:
        :class:`WalletInfo` with ``address``, ``state``, ``balance`` in TON,
        and ``usdt_balance`` in USDT.

    Raises:
        WalletError: If the wallet state cannot be fetched.
    """
    async with TonapiClient(network=NetworkGlobalID.MAINNET, api_key=client.api_key) as ton:
        try:
            wallet_cls = WALLET_CLASSES[client.wallet_version]
            wallet, _, _, _ = wallet_cls.from_mnemonic(client=ton, mnemonic=client.seed)
            await wallet.refresh()
            wallet_address = wallet.address.to_str(False, False)
            usdt_balance = await get_usdt_balance(ton, wallet_address)
            return WalletInfo(
                address=wallet.address.to_str(is_user_friendly=True, is_bounceable=False),
                state=wallet.state.value,
                ton_balance=round(wallet.balance / 1_000_000_000, 4),
                usdt_balance=round(usdt_balance, 4),
            )
        except Exception as exc:
            raise WalletError(WalletError.WALLET_INFO_FAILED.format(exc=exc)) from exc
