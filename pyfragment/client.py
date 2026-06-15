from __future__ import annotations

from typing import Any

from pyfragment.core.constants import BASE_HEADERS, DEFAULT_TIMEOUT, FRAGMENT_BASE_URL
from pyfragment.core.validation import (
    normalize_provider,
    normalize_wallet_version,
    parse_cookies,
    validate_cookie_keys,
    validate_credentials,
)
from pyfragment.domains.ads.models import AdsRechargeResult, AdsTopupResult
from pyfragment.domains.ads.service import AdsService
from pyfragment.domains.anonymous_numbers.models import LoginCodeResult, TerminateSessionsResult
from pyfragment.domains.anonymous_numbers.service import AnonymousNumbersService
from pyfragment.domains.base import raw_api_call
from pyfragment.domains.giveaways.models import PremiumGiveawayResult, StarsGiveawayResult
from pyfragment.domains.giveaways.service import GiveawaysService
from pyfragment.domains.marketplace.models import GiftsResult, NumbersResult, UsernamesResult
from pyfragment.domains.marketplace.service import MarketplaceService
from pyfragment.domains.purchases.models import PremiumResult, StarsResult
from pyfragment.domains.purchases.service import PurchasesService
from pyfragment.enums import ApiProvider, PaymentMethod, WalletVersion
from pyfragment.services.tonapi.models import WalletInfo
from pyfragment.services.tonapi.service import TonapiService


class FragmentClient:
    """
    Client for the Fragment.com API.

    .. note::
        This library is not affiliated with, endorsed by, or in any way officially
        connected with Fragment or Telegram.

    Args:
        seed: 12- or 24-word mnemonic phrase for the GRAM (ex TON) wallet.
        api_key: API key for the chosen provider — tonconsole.com (default) or t.me/toncenter.
        cookies: Fragment session cookies as a dict or JSON string.
        wallet_version: Wallet contract version — ``"V4R2"`` or ``"V5R1"`` (default).
        api_provider: Blockchain API provider — ``"tonapi"`` (tonconsole.com, default)
            or ``"toncenter"`` (t.me/toncenter).
        timeout: HTTP request timeout in seconds. Defaults to ``30.0``.
        headers: Custom HTTP request headers. If omitted, :data:`BASE_HEADERS` is used.

    Raises:
        ConfigurationError: If ``seed``, ``api_key``, ``wallet_version``, or ``api_provider``
            are missing or invalid.
        CookieError: If ``cookies`` cannot be parsed or are missing required keys.

    Example::

        async with FragmentClient(
            seed="word1 word2 ...",
            api_key="AAABBB...",
            cookies={"stel_ssid": "...", "stel_dt": "...", ...},
        ) as client:
            print(await client.get_wallet())
            result = await client.purchase_premium("@username", months=6)
            print(result.transaction_id)
    """

    def __init__(
        self,
        seed: str,
        api_key: str,
        cookies: dict[str, Any] | str,
        wallet_version: str = "V5R1",
        api_provider: str = "tonapi",
        timeout: float = DEFAULT_TIMEOUT,
        headers: dict[str, str] | None = None,
    ) -> None:
        validate_credentials(seed, api_key)
        provider = normalize_provider(api_provider)
        parsed_cookies = parse_cookies(cookies)
        validate_cookie_keys(parsed_cookies)
        version = normalize_wallet_version(wallet_version)

        self.seed: str = seed.strip()
        self.api_key: str = api_key.strip()
        self.api_provider: ApiProvider = provider
        self.cookies: dict[str, Any] = parsed_cookies
        self.wallet_version: WalletVersion = version
        self.timeout: float = timeout
        self.headers: dict[str, str] = headers if headers is not None else BASE_HEADERS
        self.marketplace = MarketplaceService(self)
        self.purchases = PurchasesService(self)
        self.giveaways = GiveawaysService(self)
        self.tonapi = TonapiService(self)
        self.anonymous_numbers = AnonymousNumbersService(self)
        self.ads = AdsService(self)

    async def __aenter__(self) -> FragmentClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        pass

    def __repr__(self) -> str:
        return f"FragmentClient(wallet_version='{self.wallet_version}', api_provider='{self.api_provider}', cookies={len(self.cookies)} keys)"

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
            :class:`PremiumResult` with ``transaction_id``, ``username``, and ``amount``.
        """
        return await self.purchases.purchase_premium(username, months, show_sender=show_sender, payment_method=payment_method)

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
            :class:`StarsResult` with ``transaction_id``, ``username``, and ``amount``.
        """
        return await self.purchases.purchase_stars(username, amount, show_sender=show_sender, payment_method=payment_method)

    async def topup_gram(self, username: str, amount: int, show_sender: bool = True) -> AdsTopupResult:
        """Top up GRAM (ex TON) to a recipient's Telegram balance.

        Args:
            username: Recipient's Telegram username (with or without ``@``).
            amount: Amount in GRAM (ex TON) — integer from ``1`` to ``1 000 000 000``.
            show_sender: Show your name as the sender. Defaults to ``True``.

        Returns:
            :class:`AdsTopupResult` with ``transaction_id``, ``username``, and ``amount``.
        """
        return await self.ads.topup_gram(username, amount, show_sender=show_sender)

    async def recharge_ads(self, account: str, amount: int) -> AdsRechargeResult:
        """Add funds to your own Telegram Ads account.

        Args:
            account: Channel or bot username the Ads account is linked to (e.g. ``"@mychannel"``).
            amount: Amount in GRAM (ex TON) — integer from ``1`` to ``1 000 000 000``.

        Returns:
            :class:`AdsRechargeResult` with ``transaction_id`` and ``amount``.
        """
        return await self.ads.recharge_ads(account, amount)

    async def get_wallet(self) -> WalletInfo:
        """Return the address, state, and balances of the wallet.

        Returns:
            :class:`WalletInfo` with ``address``, ``state``, ``gram_balance``, and ``usdt_balance``.
        """
        return await self.tonapi.get_wallet()

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
            winners: Number of winners — integer from ``1`` to ``15``.
            amount: Stars each winner receives — integer from ``500`` to ``1 000 000``.
            payment_method: Payment currency — defaults to ``PaymentMethod.GRAM``.

        Returns:
            :class:`StarsGiveawayResult` with ``transaction_id``, ``channel``, ``winners``, and ``amount``.
        """
        return await self.giveaways.giveaway_stars(channel, winners, amount, payment_method=payment_method)

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
        return await self.giveaways.giveaway_premium(channel, winners, months, payment_method=payment_method)

    async def get_login_code(self, number: str) -> LoginCodeResult:
        """Fetch the current pending login code for an anonymous number.

        Args:
            number: Phone number with or without leading ``+``.

        Returns:
            :class:`LoginCodeResult` with ``number``, ``code`` (``None`` if none pending),
            and ``active_sessions`` count.
        """
        return await self.anonymous_numbers.get_login_code(number)

    async def toggle_login_codes(self, number: str, can_receive: bool) -> None:
        """Enable or disable login code delivery for an anonymous number.

        Args:
            number: Phone number with or without leading ``+``.
            can_receive: ``True`` to allow receiving codes, ``False`` to block them.
        """
        return await self.anonymous_numbers.toggle_login_codes(number, can_receive)

    async def terminate_sessions(self, number: str) -> TerminateSessionsResult:
        """Terminate all active Telegram sessions for an anonymous number.

        Args:
            number: Phone number with or without leading ``+``.

        Returns:
            :class:`TerminateSessionsResult` with ``number`` and ``message``.

        Raises:
            AnonymousNumberError: If the number is not owned or has no active sessions.
        """
        return await self.anonymous_numbers.terminate_sessions(number)

    async def search_usernames(
        self,
        query: str = "",
        sort: str | None = None,
        filter: str | None = None,
        offset_id: str | None = None,
    ) -> UsernamesResult:
        """Search the Fragment marketplace for Telegram usernames.

        Args:
            query: Search text. Omit or pass ``""`` to browse all.
            sort: ``"price_desc"``, ``"price_asc"``, ``"listed"``, or ``"ending"``.
            filter: ``"auction"``, ``"sale"``, ``"sold"``, or ``""`` (available).
            offset_id: Pass :attr:`UsernamesResult.next_offset_id` to fetch the next page.

        Returns:
            :class:`UsernamesResult` with ``items`` and ``next_offset_id``.
        """
        return await self.marketplace.search_usernames(query, sort=sort, filter=filter, offset_id=offset_id)

    async def search_numbers(
        self,
        query: str = "",
        sort: str | None = None,
        filter: str | None = None,
        offset_id: str | None = None,
    ) -> NumbersResult:
        """Search the Fragment marketplace for anonymous Telegram numbers.

        Args:
            query: Search text. Omit or pass ``""`` to browse all.
            sort: ``"price_desc"``, ``"price_asc"``, ``"listed"``, or ``"ending"``.
            filter: ``"auction"``, ``"sale"``, ``"sold"``, or ``""`` (available).
            offset_id: Pass :attr:`NumbersResult.next_offset_id` to fetch the next page.

        Returns:
            :class:`NumbersResult` with ``items`` and ``next_offset_id``.
        """
        return await self.marketplace.search_numbers(query, sort=sort, filter=filter, offset_id=offset_id)

    async def search_gifts(
        self,
        query: str = "",
        collection: str | None = None,
        sort: str | None = None,
        filter: str | None = None,
        view: str | None = None,
        attr: dict[str, list[str]] | None = None,
        offset: int | None = None,
    ) -> GiftsResult:
        """Search the Fragment gifts marketplace.

        Args:
            query: Search text. Omit or pass ``""`` to browse all.
            collection: Gift collection slug (e.g. ``"artisanbrick"``).
            sort: ``"price_desc"``, ``"price_asc"``, ``"listed"``, or ``"ending"``.
            filter: ``"auction"``, ``"sale"``, ``"sold"``, or ``""`` (available).
            view: Active attribute tab name (e.g. ``"Model"``).
            attr: Attribute filters — e.g. ``{"Model": ["Foosball"], "Backdrop": ["Celtic Blue"]}``.
            offset: Pass :attr:`GiftsResult.next_offset` to fetch the next page.

        Returns:
            :class:`GiftsResult` with ``items`` and ``next_offset``.
        """
        return await self.marketplace.search_gifts(
            query, collection=collection, sort=sort, filter=filter, view=view, attr=attr, offset=offset
        )

    async def call(
        self, method: str, data: dict[str, Any] | None = None, *, page_url: str = FRAGMENT_BASE_URL
    ) -> dict[str, Any]:
        """Send a raw request to the Fragment API.

        Args:
            method: Fragment API method name, e.g. ``"searchPremiumGiftRecipient"``.
            data: Additional form-data fields.
            page_url: Fragment page URL to derive the API hash. Defaults to ``FRAGMENT_BASE_URL``.

        Returns:
            Raw parsed JSON response as a dict.
        """
        return await raw_api_call(self.cookies, self.timeout, method, data, page_url, self.headers)
