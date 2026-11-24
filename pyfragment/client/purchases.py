from __future__ import annotations

from decimal import Decimal

from pyfragment.client.base import BaseClient
from pyfragment.domains.giveaways.models import PremiumGiveawayResult, StarsGiveawayResult
from pyfragment.domains.giveaways.premium import giveaway_premium
from pyfragment.domains.giveaways.stars import giveaway_stars
from pyfragment.domains.purchases.models import PremiumPackage, PremiumResult, StarsPackage, StarsResult
from pyfragment.domains.purchases.premium import check_premium_recipient, get_premium_packages, purchase_premium
from pyfragment.domains.purchases.stars import (
    check_stars_recipient,
    get_stars_packages,
    get_stars_price,
    purchase_stars,
)
from pyfragment.domains.recipients import Recipient
from pyfragment.enums import PaymentMethod


class PurchaseMethods(BaseClient):
    async def purchase_premium(
        self,
        username: str,
        months: int,
        show_sender: bool = True,
        payment_method: PaymentMethod = PaymentMethod.GRAM,
    ) -> PremiumResult:
        """Gift Telegram Premium to a user.

        Args:
            username: Recipient identifier — ``@username``, ``username``, or ``https://t.me/username``.
            months: Duration — ``3``, ``6``, or ``12``.
            show_sender: Show your name as the sender. Defaults to ``True``.
            payment_method: Payment currency — defaults to ``PaymentMethod.GRAM``.

        Returns:
            :class:`PremiumResult` with ``transaction_id``, ``username``, ``amount``, ``confirmed``, and ``comment``.
        """
        return await purchase_premium(self, username, months, show_sender=show_sender, payment_method=payment_method)

    async def purchase_stars(
        self,
        username: str,
        amount: int,
        show_sender: bool = True,
        payment_method: PaymentMethod = PaymentMethod.GRAM,
    ) -> StarsResult:
        """Send Telegram Stars to a user.

        Args:
            username: Recipient identifier — ``@username``, ``username``, or ``https://t.me/username``.
            amount: Number of stars — integer from ``50`` to ``10 000 000``.
            show_sender: Show your name as the gift sender. Defaults to ``True``.
            payment_method: Payment currency — defaults to ``PaymentMethod.GRAM``.

        Returns:
            :class:`StarsResult` with ``transaction_id``, ``username``, ``amount``, ``confirmed``, and ``comment``.
        """
        return await purchase_stars(self, username, amount, show_sender=show_sender, payment_method=payment_method)

    async def get_stars_price(self, amount: int) -> Decimal:
        """Return the current GRAM price for ``amount`` Stars.

        Useful for pre-checking the wallet balance before calling :meth:`purchase_stars`.

        Args:
            amount: Number of stars — integer from ``50`` to ``10 000 000``.

        Returns:
            Price in GRAM as a :class:`~decimal.Decimal`.
        """
        return await get_stars_price(self, amount)

    async def get_stars_packages(self) -> list[StarsPackage]:
        """Return all predefined Stars purchase packages with current GRAM and USD prices.

        Returns:
            List of :class:`StarsPackage` with ``stars``, ``gram``, and ``usd`` fields.
        """
        return await get_stars_packages(self)

    async def get_premium_packages(self) -> list[PremiumPackage]:
        """Return all Telegram Premium subscription options with current GRAM and USD prices.

        Returns:
            List of :class:`PremiumPackage` with ``months``, ``gram``, and ``usd`` fields.
            Ordered by the page (12 → 6 → 3 months).
        """
        return await get_premium_packages(self)

    async def check_stars_recipient(self, username: str) -> Recipient:
        """Check that a user can receive Stars, without buying anything.

        Raises:
            UserNotFoundError: If the username doesn't belong to a Telegram user.
        """
        return await check_stars_recipient(self, username)

    async def check_premium_recipient(self, username: str, months: int = 3) -> Recipient:
        """Check that a user can be gifted Premium for ``months``, without buying anything.

        Raises:
            UserNotFoundError: If the username doesn't belong to a Telegram user.
            AlreadySubscribedError: If the user already has Premium.
        """
        return await check_premium_recipient(self, username, months)

    async def giveaway_stars(
        self,
        channel: str,
        winners: int,
        amount: int,
        payment_method: PaymentMethod = PaymentMethod.GRAM,
    ) -> StarsGiveawayResult:
        """Run a Telegram Stars giveaway for a channel.

        Args:
            channel: Channel identifier — ``@channel``, ``channel``, or ``https://t.me/channel``.
            winners: Number of winners — integer from ``1`` to ``5``.
            amount: Stars each winner receives — integer from ``500`` to ``1 000 000``.
            payment_method: Payment currency — defaults to ``PaymentMethod.GRAM``.

        Returns:
            :class:`StarsGiveawayResult` with ``transaction_id``, ``channel``, ``winners``, and ``amount``.
        """
        return await giveaway_stars(self, channel, winners, amount, payment_method=payment_method)

    async def giveaway_premium(
        self,
        channel: str,
        winners: int,
        months: int = 3,
        payment_method: PaymentMethod = PaymentMethod.GRAM,
    ) -> PremiumGiveawayResult:
        """Run a Telegram Premium giveaway for a channel.

        Args:
            channel: Channel identifier — ``@channel``, ``channel``, or ``https://t.me/channel``.
            winners: Number of winners — integer from ``1`` to ``24 000``.
            months: Premium duration per winner — ``3``, ``6``, or ``12``. Defaults to ``3``.
            payment_method: Payment currency — defaults to ``PaymentMethod.GRAM``.

        Returns:
            :class:`PremiumGiveawayResult` with ``transaction_id``, ``channel``, ``winners``, and ``amount``.
        """
        return await giveaway_premium(self, channel, winners, months, payment_method=payment_method)
