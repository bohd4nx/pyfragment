from __future__ import annotations

from datetime import datetime

from pyfragment.domains.base import BaseService
from pyfragment.domains.wallet.balance import get_wallet_info
from pyfragment.domains.wallet.lookup import find_transfer
from pyfragment.domains.wallet.models import TransferInfo, WalletInfo


class WalletService(BaseService):
    async def get_wallet(self) -> WalletInfo:
        return await get_wallet_info(self._client)

    async def find_transfer(
        self, *, msg_hash: str | None = None, comment: str | None = None, since: datetime
    ) -> TransferInfo | None:
        return await find_transfer(self._client, msg_hash=msg_hash, comment=comment, since=since)
