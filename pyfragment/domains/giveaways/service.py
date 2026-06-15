from __future__ import annotations

from typing import TYPE_CHECKING

from pyfragment.domains.base import BaseService
from pyfragment.domains.giveaways.giveaway import giveaway_premium, giveaway_stars
from pyfragment.domains.giveaways.models import PremiumGiveawayResult, StarsGiveawayResult
from pyfragment.enums import PaymentMethod

if TYPE_CHECKING:
    pass


class GiveawaysService(BaseService):
    async def giveaway_stars(
        self,
        channel: str,
        winners: int,
        amount: int,
        payment_method: PaymentMethod = PaymentMethod.GRAM,
    ) -> StarsGiveawayResult:
        return await giveaway_stars(self._client, channel, winners, amount, payment_method=payment_method)

    async def giveaway_premium(
        self,
        channel: str,
        winners: int,
        months: int = 3,
        payment_method: PaymentMethod = PaymentMethod.GRAM,
    ) -> PremiumGiveawayResult:
        return await giveaway_premium(self._client, channel, winners, months, payment_method=payment_method)
