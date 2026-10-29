from __future__ import annotations

from pyfragment.domains.base import BaseService
from pyfragment.domains.purchases.models import PremiumResult, StarsResult
from pyfragment.domains.purchases.premium import check_premium_recipient, purchase_premium
from pyfragment.domains.purchases.stars import check_stars_recipient, purchase_stars
from pyfragment.domains.recipients import Recipient
from pyfragment.enums import PaymentMethod


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

    async def check_stars_recipient(self, username: str) -> Recipient:
        return await check_stars_recipient(self._client, username)

    async def check_premium_recipient(self, username: str, months: int = 3) -> Recipient:
        return await check_premium_recipient(self._client, username, months)
