from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from decimal import Decimal
from typing import Any

from pyfragment.constants import (
    BASE_HEADERS,
    CONFIRM_STATE_TIMEOUT,
    DEFAULT_GAS_RESERVE,
    DEFAULT_TIMEOUT,
    FRAGMENT_BASE_URL,
    PROFILE_PAGE,
)
from pyfragment.domains.ads.models import AdsRechargeResult, AdsTopupResult
from pyfragment.domains.ads.service import AdsService
from pyfragment.domains.anonymous_numbers.models import LoginCodeResult, TerminateSessionsResult
from pyfragment.domains.anonymous_numbers.service import AnonymousNumbersService
from pyfragment.domains.assets.models import MyGiftsResult, MyNumbersResult, MyUsernamesResult
from pyfragment.domains.assets.service import AssetsService
from pyfragment.domains.giveaways.models import PremiumGiveawayResult, StarsGiveawayResult
from pyfragment.domains.giveaways.service import GiveawaysService
from pyfragment.domains.marketplace.models import GiftsResult, NumbersResult, UsernamesResult
from pyfragment.domains.marketplace.service import MarketplaceService
from pyfragment.domains.purchases.models import PremiumPackage, PremiumResult, StarsPackage, StarsResult
from pyfragment.domains.purchases.service import PurchasesService
from pyfragment.domains.recipients import Recipient
from pyfragment.domains.wallet.models import TransferIntent, WalletInfo
from pyfragment.domains.wallet.service import WalletService
from pyfragment.domains.wallet.wallet import TonWallet
from pyfragment.enums import ApiMethod, ApiProvider, AuctionFilter, AuctionSort, MnemonicType, PaymentMethod, WalletVersion
from pyfragment.exceptions import FragmentAPIError
from pyfragment.schemas import error_text
from pyfragment.transport import FragmentTransport
from pyfragment.utils.validation import (
    normalize_confirm_timeout,
    normalize_gas_reserve,
    normalize_mnemonic_type,
    normalize_provider,
    normalize_seed,
    normalize_wallet_version,
    parse_cookies,
    validate_cookie_keys,
    validate_credentials,
    validate_seed,
)


class FragmentClient:
    """
    Client for the Fragment.com API.

    .. note::
        This library is not affiliated with, endorsed by, or in any way officially
        connected with Fragment or Telegram.

    Args:
        seed: Mnemonic phrase of the GRAM (ex TON) wallet.
        api_key: API key for the chosen provider — tonconsole.com (default) or t.me/toncenter.
        cookies: Fragment session cookies as a dict or JSON string.
        wallet_version: Wallet contract — ``"V5R1"`` (default), ``"V4R2"``, ``"HighloadV2"``,
            ``"HighloadV3R1"``, or ``"TG"`` for a Telegram Wallet (12 words, or 24 after a key rotation).
        mnemonic_type: How the phrase derives the key — ``"ton"`` (default: Tonkeeper, MyTonWallet and
            other TON wallets, 12 or 24 words) or ``"multichain"`` (a BIP-39 phrase of a multichain
            wallet, 12 to 24 words). A Telegram Wallet always uses ``"multichain"``.
        api_provider: Blockchain API provider — ``"tonapi"`` (tonconsole.com, default)
            or ``"toncenter"`` (t.me/toncenter).
        timeout: HTTP request timeout in seconds. Defaults to ``30.0``.
        headers: Custom HTTP request headers. If omitted, :data:`BASE_HEADERS` is used.
        gas_reserve: GRAM (ex TON) the wallet must keep on top of a payment for fees. Defaults to ``0.05``.
        confirm_timeout: Seconds to wait for Fragment to confirm a purchase after paying. ``0`` reports it
            right away (``confirmed=False``). Defaults to ``60``.
        on_transfer_prepared: Async callback receiving each :class:`TransferIntent` after it is signed and
            before it is sent. Save it to verify the transfer on-chain by ``msg_hash`` if the process dies
            before returning the purchase result; if it raises, nothing is sent.

    The client keeps one HTTP session and one blockchain API connection and reuses them across calls.
    Use ``async with`` (or call :meth:`aclose`) to release them when you are done.

    Purchases from one client run one at a time. Run purchases from one wallet in several processes one at a
    time too, and keep the system clock synced.

    Raises:
        ConfigurationError: If ``seed``, ``api_key``, ``wallet_version``, ``mnemonic_type``,
            ``api_provider``, ``gas_reserve`` or ``confirm_timeout`` are missing or invalid.
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
        headers: dict[str, str | None] | None = None,
        mnemonic_type: str | None = None,
        gas_reserve: Decimal | float | str = DEFAULT_GAS_RESERVE,
        confirm_timeout: float = CONFIRM_STATE_TIMEOUT,
        on_transfer_prepared: Callable[[TransferIntent], Awaitable[None]] | None = None,
    ) -> None:
        validate_credentials(seed, api_key)
        provider = normalize_provider(api_provider)
        parsed_cookies = parse_cookies(cookies)
        validate_cookie_keys(parsed_cookies)
        version = normalize_wallet_version(wallet_version)
        phrase_type = normalize_mnemonic_type(mnemonic_type, version)
        normalized_seed = normalize_seed(seed)
        validate_seed(normalized_seed, version, phrase_type)

        self.seed: str = normalized_seed
        self.api_key: str = api_key.strip()
        self.api_provider: ApiProvider = provider
        self.cookies: dict[str, Any] = parsed_cookies
        self.wallet_version: WalletVersion = version
        self.mnemonic_type: MnemonicType = phrase_type
        self.timeout: float = timeout
        self.headers: dict[str, str | None] = dict(headers) if headers is not None else dict(BASE_HEADERS)
        self.gas_reserve_nano: int = normalize_gas_reserve(gas_reserve)
        self.confirm_timeout: float = normalize_confirm_timeout(confirm_timeout)
        self.on_transfer_prepared: Callable[[TransferIntent], Awaitable[None]] | None = on_transfer_prepared
        self._transport = FragmentTransport(parsed_cookies, timeout, self.headers)
        self.ton_wallet = TonWallet(self)
        self.marketplace = MarketplaceService(self)
        self.purchases = PurchasesService(self)
        self.giveaways = GiveawaysService(self)
        self.wallet = WalletService(self)
        self.anonymous_numbers = AnonymousNumbersService(self)
        self.ads = AdsService(self)
        self.assets = AssetsService(self)

    async def __aenter__(self) -> FragmentClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close the HTTP session and the blockchain API connection. Called automatically when leaving ``async with``."""
        try:
            await self._transport.aclose()
        finally:
            await self.ton_wallet.aclose()

    def __repr__(self) -> str:
        return (
            f"FragmentClient(wallet_version='{self.wallet_version}', mnemonic_type='{self.mnemonic_type}', "
            f"api_provider='{self.api_provider}', cookies={len(self.cookies)} keys)"
        )

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
            :class:`StarsResult` with ``transaction_id``, ``username``, ``amount``, ``confirmed``, and ``comment``.
        """
        return await self.purchases.purchase_stars(username, amount, show_sender=show_sender, payment_method=payment_method)

    async def topup_gram(self, username: str, amount: int, show_sender: bool = True) -> AdsTopupResult:
        """Top up GRAM (ex TON) to a recipient's Telegram balance.

        Args:
            username: Recipient identifier — ``@username``, ``username``, or ``https://t.me/username``.
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
            :class:`WalletInfo` with ``address``, ``state``, and exact ``Decimal`` balances ``gram_balance``
            and ``usdt_balance`` (``None`` if the USDT lookup failed).
        """
        return await self.wallet.get_wallet()

    async def get_stars_price(self, amount: int) -> Decimal:
        """Return the current GRAM price for ``amount`` Stars.

        Useful for pre-checking the wallet balance before calling :meth:`purchase_stars`.

        Args:
            amount: Number of stars — integer from ``50`` to ``10 000 000``.

        Returns:
            Price in GRAM as a :class:`~decimal.Decimal`.
        """
        return await self.purchases.get_stars_price(amount)

    async def get_stars_packages(self) -> list[StarsPackage]:
        """Return all predefined Stars purchase packages with current GRAM and USD prices.

        Returns:
            List of :class:`StarsPackage` with ``stars``, ``gram``, and ``usd`` fields.
        """
        return await self.purchases.get_stars_packages()

    async def get_premium_packages(self) -> list[PremiumPackage]:
        """Return all Telegram Premium subscription options with current GRAM and USD prices.

        Returns:
            List of :class:`PremiumPackage` with ``months``, ``gram``, and ``usd`` fields.
            Ordered by the page (12 → 6 → 3 months).
        """
        return await self.purchases.get_premium_packages()

    async def logout(self) -> None:
        """End the Fragment session (invalidates session cookies server-side)."""
        result = await self.call("logOut")
        if err := error_text(result):
            raise FragmentAPIError(err)

    async def link_wallet(self) -> None:
        """Link the connected TON wallet to the Fragment account.

        Required once after connecting a wallet via TON Connect before purchases can be made.
        Uses the existing ``stel_ton_token`` cookie — no separate signing needed.
        """
        result = await self.call("linkWallet", page_url=PROFILE_PAGE)
        if err := error_text(result):
            raise FragmentAPIError(err)

    async def disconnect_wallet(self) -> None:
        """Disconnect the linked TON wallet from Fragment."""
        result = await self.call("tonLogOut")
        if err := error_text(result):
            raise FragmentAPIError(err)

    async def check_stars_recipient(self, username: str) -> Recipient:
        """Check that a user can receive Stars, without buying anything.

        Raises:
            UserNotFoundError: If the username doesn't belong to a Telegram user.
        """
        return await self.purchases.check_stars_recipient(username)

    async def check_premium_recipient(self, username: str, months: int = 3) -> Recipient:
        """Check that a user can be gifted Premium for ``months``, without buying anything.

        Raises:
            UserNotFoundError: If the username doesn't belong to a Telegram user.
            AlreadySubscribedError: If the user already has Premium.
        """
        return await self.purchases.check_premium_recipient(username, months)

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
        sort: AuctionSort | str | None = None,
        filter: AuctionFilter | str | None = None,
        offset_id: str | None = None,
    ) -> UsernamesResult:
        """Search the Fragment marketplace for Telegram usernames.

        Args:
            query: Search text. Omit or pass ``""`` to browse all.
            sort: An :class:`AuctionSort` or its value: ``"price"`` (default), ``"price_desc"``,
                ``"price_asc"``, ``"listed"``, or ``"ending"``.
            filter: An :class:`AuctionFilter` or its value: ``""`` (available, default), ``"auction"``,
                ``"sale"``, or ``"sold"``.
            offset_id: Pass :attr:`UsernamesResult.next_offset_id` to fetch the next page.

        Returns:
            :class:`UsernamesResult` with ``items`` and ``next_offset_id``.
        """
        return await self.marketplace.search_usernames(query, sort=sort, filter=filter, offset_id=offset_id)

    async def search_numbers(
        self,
        query: str = "",
        sort: AuctionSort | str | None = None,
        filter: AuctionFilter | str | None = None,
        offset_id: str | None = None,
    ) -> NumbersResult:
        """Search the Fragment marketplace for anonymous Telegram numbers.

        Args:
            query: Search text. Omit or pass ``""`` to browse all.
            sort: An :class:`AuctionSort` or its value: ``"price"`` (default), ``"price_desc"``,
                ``"price_asc"``, ``"listed"``, or ``"ending"``.
            filter: An :class:`AuctionFilter` or its value: ``""`` (available, default), ``"auction"``,
                ``"sale"``, or ``"sold"``.
            offset_id: Pass :attr:`NumbersResult.next_offset_id` to fetch the next page.

        Returns:
            :class:`NumbersResult` with ``items`` and ``next_offset_id``.
        """
        return await self.marketplace.search_numbers(query, sort=sort, filter=filter, offset_id=offset_id)

    async def search_gifts(
        self,
        query: str = "",
        collection: str | None = None,
        sort: AuctionSort | str | None = None,
        filter: AuctionFilter | str | None = None,
        view: str | None = None,
        attr: Mapping[str, Sequence[str]] | None = None,
        offset: int | None = None,
    ) -> GiftsResult:
        """Search the Fragment gifts marketplace.

        Args:
            query: Search text. Omit or pass ``""`` to browse all.
            collection: Gift collection slug (e.g. ``"artisanbrick"``).
            sort: An :class:`AuctionSort` or its value: ``"price"`` (default), ``"price_desc"``,
                ``"price_asc"``, ``"listed"``, or ``"ending"``.
            filter: An :class:`AuctionFilter` or its value: ``""`` (available, default), ``"auction"``,
                ``"sale"``, or ``"sold"``.
            view: Active attribute tab name (e.g. ``"Model"``).
            attr: Trait filters keyed by :class:`GiftAttribute` name (``Model``, ``Backdrop`` or ``Symbol``,
                any casing) — e.g. ``{"Model": ["Foosball"], "Backdrop": ["Celtic Blue"]}``.
            offset: Pass :attr:`GiftsResult.next_offset` to fetch the next page.

        Returns:
            :class:`GiftsResult` with ``items`` and ``next_offset``.
        """
        return await self.marketplace.search_gifts(
            query, collection=collection, sort=sort, filter=filter, view=view, attr=attr, offset=offset
        )

    async def get_my_usernames(self) -> MyUsernamesResult:
        """List Telegram usernames owned by the authenticated account.

        Returns:
            :class:`MyUsernamesResult` with an ``items`` list of :class:`AuctionItem`.
        """
        return await self.assets.get_my_usernames()

    async def get_my_numbers(self) -> MyNumbersResult:
        """List anonymous phone numbers owned by the authenticated account.

        Returns:
            :class:`MyNumbersResult` with an ``items`` list of :class:`AuctionItem`.
        """
        return await self.assets.get_my_numbers()

    async def get_my_gifts(self) -> MyGiftsResult:
        """List Telegram gifts owned by the authenticated account.

        Returns:
            :class:`MyGiftsResult` with an ``items`` list of :class:`AuctionItem`.
        """
        return await self.assets.get_my_gifts()

    async def call(
        self, method: ApiMethod | str, data: dict[str, Any] | None = None, *, page_url: str = FRAGMENT_BASE_URL
    ) -> dict[str, Any]:
        """Send a raw request to the Fragment API.

        Args:
            method: Fragment API method name, e.g. ``"searchPremiumGiftRecipient"``.
            data: Additional form-data fields.
            page_url: Fragment page URL to derive the API hash. Defaults to ``FRAGMENT_BASE_URL``.

        Returns:
            Raw parsed JSON response as a dict.
        """
        return await self._transport.call(method, data, page_url)
