from __future__ import annotations

import base64
from typing import TYPE_CHECKING, Any

from ton_core import NetworkGlobalID
from tonutils.clients import TonapiClient

from pyfragment.core.constants import WALLET_CLASSES
from pyfragment.domains.tonapi.balance import get_usdt_balance
from pyfragment.exceptions import WalletError
from pyfragment.models.wallet import WalletInfo

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


async def get_account_info(client: FragmentClient) -> dict[str, Any]:
    """Build the wallet payload Fragment needs to prepare a transaction.

    Args:
        client: Authenticated `FragmentClient` instance with seed and API key.

    Returns:
        A JSON-serialisable dictionary containing address, public key, chain,
        and wallet state-init bytes.
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
    """Fetch the wallet address, chain state, and TON/USDT balances.

    Args:
        client: Authenticated `FragmentClient` instance with seed and API key.

    Returns:
        `WalletInfo` with the friendly wallet address, current state,
        TON balance, and USDT balance.
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
