from __future__ import annotations

from pyfragment.domains.base import BaseService
from pyfragment.domains.wallet.balance import get_wallet_info
from pyfragment.domains.wallet.models import WalletInfo


class WalletService(BaseService):
    async def get_wallet(self) -> WalletInfo:
        return await get_wallet_info(self._client)
