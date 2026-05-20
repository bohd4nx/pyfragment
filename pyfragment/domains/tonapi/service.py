from __future__ import annotations

from typing import TYPE_CHECKING

from pyfragment.domains.base import BaseService
from pyfragment.domains.tonapi.info import get_wallet_info
from pyfragment.models.wallet import WalletInfo

if TYPE_CHECKING:
    pass


class TonapiService(BaseService):
    async def get_wallet(self) -> WalletInfo:
        return await get_wallet_info(self._client)
