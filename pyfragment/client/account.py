from __future__ import annotations

from pyfragment.client.base import BaseClient
from pyfragment.constants.fragment import PROFILE_PAGE
from pyfragment.domains.assets.models import MyGiftsResult, MyNumbersResult, MyUsernamesResult
from pyfragment.domains.assets.owned import get_my_gifts, get_my_numbers, get_my_usernames
from pyfragment.domains.wallet.balance import get_wallet_info
from pyfragment.domains.wallet.models import WalletInfo
from pyfragment.schemas import raise_for_error


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
