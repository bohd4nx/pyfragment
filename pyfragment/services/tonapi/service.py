from __future__ import annotations

from pyfragment.domains.base import BaseService
from pyfragment.services.tonapi.account import get_wallet_info
from pyfragment.services.tonapi.models import WalletInfo


class TonapiService(BaseService):
    async def get_wallet(self) -> WalletInfo:
        return await get_wallet_info(self._client)
