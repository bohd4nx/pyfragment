from __future__ import annotations

from typing import TYPE_CHECKING

from pyfragment.domains.base import BaseService
from pyfragment.domains.wallet.info import get_wallet_info
from pyfragment.domains.wallet.topup import topup_ton
from pyfragment.models.payments import AdsTopupResult
from pyfragment.models.wallet import WalletInfo

if TYPE_CHECKING:
    pass


class WalletService(BaseService):
    async def get_wallet(self) -> WalletInfo:
        return await get_wallet_info(self._client)

    async def topup_ton(self, username: str, amount: int, show_sender: bool = True) -> AdsTopupResult:
        return await topup_ton(self._client, username, amount, show_sender=show_sender)
