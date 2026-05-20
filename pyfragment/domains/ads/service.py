from __future__ import annotations

from typing import TYPE_CHECKING

from pyfragment.domains.ads.recharge import recharge_ads
from pyfragment.domains.base import BaseService
from pyfragment.models.payments import AdsRechargeResult

if TYPE_CHECKING:
    pass


class AdsService(BaseService):
    async def recharge_ads(self, account: str, amount: int) -> AdsRechargeResult:
        return await recharge_ads(self._client, account, amount)
