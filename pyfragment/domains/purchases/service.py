from __future__ import annotations

from typing import TYPE_CHECKING

from pyfragment.domains.base import BaseService
from pyfragment.domains.purchases.models import PremiumResult, StarsResult
from pyfragment.domains.purchases.purchase import purchase_premium, purchase_stars
from pyfragment.enums import PaymentMethod

if TYPE_CHECKING:
    pass


class PurchasesService(BaseService):
    async def purchase_stars(
        self,
        username: str,
        amount: int,
        show_sender: bool = True,
        payment_method: PaymentMethod = PaymentMethod.GRAM,
    ) -> StarsResult:
        return await purchase_stars(self._client, username, amount, show_sender=show_sender, payment_method=payment_method)

    async def purchase_premium(
        self,
        username: str,
        months: int,
        show_sender: bool = True,
        payment_method: PaymentMethod = PaymentMethod.GRAM,
    ) -> PremiumResult:
        return await purchase_premium(self._client, username, months, show_sender=show_sender, payment_method=payment_method)
