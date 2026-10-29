from __future__ import annotations

from decimal import Decimal

from pyfragment.domains.base import BaseService
from pyfragment.domains.purchases.models import PremiumPackage, PremiumResult, StarsPackage, StarsResult
from pyfragment.domains.purchases.premium import check_premium_recipient, get_premium_packages, purchase_premium
from pyfragment.domains.purchases.stars import check_stars_recipient, get_stars_packages, get_stars_price, purchase_stars
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

    async def get_stars_price(self, amount: int) -> Decimal:
        return await get_stars_price(self._client, amount)

    async def get_stars_packages(self) -> list[StarsPackage]:
        return await get_stars_packages(self._client)

    async def check_stars_recipient(self, username: str) -> Recipient:
        return await check_stars_recipient(self._client, username)

    async def get_premium_packages(self) -> list[PremiumPackage]:
        return await get_premium_packages(self._client)

    async def check_premium_recipient(self, username: str, months: int = 3) -> Recipient:
        return await check_premium_recipient(self._client, username, months)
