from __future__ import annotations

from pyfragment.client.base import BaseClient
from pyfragment.constants.fragment import PROFILE_PAGE
from pyfragment.domains.assets.models import MyGiftsResult, MyNumbersResult, MyUsernamesResult
from pyfragment.domains.assets.owned import get_my_gifts, get_my_numbers, get_my_usernames
from pyfragment.domains.history import PremiumHistoryEntry, StarsHistoryEntry, get_premium_history, get_stars_history
from pyfragment.domains.wallet.balance import get_wallet_info
from pyfragment.domains.wallet.models import WalletInfo
from pyfragment.enums import ApiError
from pyfragment.exceptions import WalletAlreadyLinkedError
from pyfragment.utils.errors import has_error, raise_for_error


class AccountMethods(BaseClient):
    async def get_wallet(self) -> WalletInfo:
        """Return the address, state, and balances of the wallet.

        Returns:
            :class:`WalletInfo` with ``address``, ``state``, and exact ``Decimal`` balances ``gram_balance``
            and ``usdt_balance`` (``None`` if the USDT lookup failed).
        """
        return await get_wallet_info(self)

    async def logout(self) -> None:
        """End the Fragment session (invalidates session cookies server-side)."""
        result = await self.call("logOut")
        raise_for_error(result)

    async def link_wallet(self) -> None:
        """Link the connected TON wallet to the Fragment account.

        Required once after connecting a wallet via TON Connect before purchases can be made.
        Uses the existing ``stel_ton_token`` cookie — no separate signing needed.
        """
        result = await self.call("linkWallet", page_url=PROFILE_PAGE)
        if has_error(result, ApiError.WALLET_ALREADY_LINKED):
            raise WalletAlreadyLinkedError(WalletAlreadyLinkedError.LINKED)
        raise_for_error(result)

    async def disconnect_wallet(self) -> None:
        """Disconnect the linked TON wallet from Fragment."""
        result = await self.call("tonLogOut")
        raise_for_error(result)

    async def get_my_usernames(self) -> MyUsernamesResult:
        """List Telegram usernames owned by the authenticated account.

        Returns:
            :class:`MyUsernamesResult` with an ``items`` list of :class:`AuctionItem`.
        """
        return await get_my_usernames(self)

    async def get_my_numbers(self) -> MyNumbersResult:
        """List anonymous phone numbers owned by the authenticated account.

        Returns:
            :class:`MyNumbersResult` with an ``items`` list of :class:`AuctionItem`.
        """
        return await get_my_numbers(self)

    async def get_my_gifts(self) -> MyGiftsResult:
        """List Telegram gifts owned by the authenticated account.

        Returns:
            :class:`MyGiftsResult` with an ``items`` list of :class:`AuctionItem`.
        """
        return await get_my_gifts(self)

    async def get_stars_history(self, newest_first: bool = True) -> list[StarsHistoryEntry]:
        """List the Stars the account has bought, as fragment.com/stars/history shows them.

        Fragment lists at most 1000 purchases per order: call with both orders to reach further back.

        Args:
            newest_first: Newest purchase first (default), or oldest first.

        Returns:
            List of :class:`StarsHistoryEntry` with ``username`` (``None`` for a recipient shown by name only), ``name``, ``stars``, ``gram`` and ``date``.
        """
        return await get_stars_history(self, newest_first)

    async def get_premium_history(self, newest_first: bool = True) -> list[PremiumHistoryEntry]:
        """List the Premium gifts the account has bought, as fragment.com/premium/history shows them.

        Args:
            newest_first: Newest gift first (default), or oldest first.

        Returns:
            List of :class:`PremiumHistoryEntry` with ``username`` (``None`` for a recipient shown by name only), ``name``, ``months``, ``gram`` and ``date``.
        """
        return await get_premium_history(self, newest_first)
