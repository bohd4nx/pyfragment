from __future__ import annotations

import logging
from decimal import Decimal
from http import HTTPStatus
from typing import TYPE_CHECKING

from ton_core import to_amount
from tonutils.clients.protocol import ClientProtocol
from tonutils.contracts.jetton import get_wallet_address_get_method, get_wallet_data_get_method
from tonutils.exceptions import ProviderResponseError, RunGetMethodError

from pyfragment.constants.chain import GRAM_DECIMALS, TVM_EXIT_ACCOUNT_NOT_FOUND, USDT_DECIMALS, USDT_GRAM_MASTER_ADDRESS
from pyfragment.domains.wallet.models import WalletInfo
from pyfragment.exceptions import ProviderError

if TYPE_CHECKING:
    from pyfragment.client.base import BaseClient
    from pyfragment.domains.wallet.wallet import TonWallet


logger = logging.getLogger(__name__)


def is_missing_jetton_wallet(exc: Exception) -> bool:
    """Whether the owner simply has no USDT jetton wallet yet: tonapi answers 404, toncenter a TVM exit code -13."""
    if isinstance(exc, ProviderResponseError):
        return exc.code == HTTPStatus.NOT_FOUND
    return isinstance(exc, RunGetMethodError) and exc.exit_code == TVM_EXIT_ACCOUNT_NOT_FOUND


async def get_usdt_balance(ton: ClientProtocol, wallet_address: str) -> int:
    """The USDT balance of a GRAM (ex TON) wallet, in units of 10^-6 USDT. Raises ``ProviderError`` if it can't be read."""
    try:
        jetton_wallet_address = await get_wallet_address_get_method(
            client=ton, address=USDT_GRAM_MASTER_ADDRESS, owner_address=wallet_address
        )
        wallet_data = await get_wallet_data_get_method(client=ton, address=jetton_wallet_address)
        return int(wallet_data[0]) if wallet_data else 0
    except Exception as exc:
        if is_missing_jetton_wallet(exc):
            logger.debug("No USDT jetton wallet, treating balance as 0 (address=%s)", wallet_address)
            return 0
        raise ProviderError.from_exception(ProviderError.BALANCE_CHECK_FAILED, exc, currency="USDT") from exc


async def get_wallet_info(client: BaseClient) -> WalletInfo:
    ton_wallet = client.ton_wallet
    try:
        onchain = await ton_wallet.state()
    except Exception as exc:
        raise ProviderError.from_exception(ProviderError.WALLET_INFO_FAILED, exc) from exc
    return WalletInfo(
        address=ton_wallet.wallet().address.to_str(is_user_friendly=True, is_bounceable=False),
        state=onchain.state.value,
        gram_balance=to_amount(int(onchain.balance), GRAM_DECIMALS, precision=GRAM_DECIMALS),
        usdt_balance=await usdt_balance_or_none(ton_wallet),
    )


async def usdt_balance_or_none(ton_wallet: TonWallet) -> Decimal | None:
    """The USDT balance, or ``None`` when the lookup failed: the GRAM balance is not lost over it, and unknown is not 0."""
    try:
        units = await get_usdt_balance(await ton_wallet.ton(), ton_wallet.address)
    except ProviderError:
        logger.debug("USDT balance check failed (address=%s)", ton_wallet.address, exc_info=True)
        return None
    return to_amount(units, USDT_DECIMALS, precision=USDT_DECIMALS)
