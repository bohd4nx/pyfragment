from __future__ import annotations

from typing import TYPE_CHECKING

from pyfragment.domains.ads.recharge import recharge_ads
from pyfragment.domains.ads.tonup import topup_gram
from pyfragment.domains.base import BaseService
from pyfragment.models.payments import AdsRechargeResult, AdsTopupResult

if TYPE_CHECKING:
    pass


class AdsService(BaseService):
    async def recharge_ads(self, account: str, amount: int) -> AdsRechargeResult:
        return await recharge_ads(self._client, account, amount)

    async def topup_gram(self, username: str, amount: int, show_sender: bool = True) -> AdsTopupResult:
        return await topup_gram(self._client, username, amount, show_sender=show_sender)
