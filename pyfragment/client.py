from __future__ import annotations

import json
from typing import Any, cast

import httpx

from pyfragment.methods.anonymous_number import get_login_code, terminate_sessions, toggle_login_codes
from pyfragment.methods.giveaway_premium import giveaway_premium
from pyfragment.methods.giveaway_stars import giveaway_stars
from pyfragment.methods.purchase_premium import purchase_premium
from pyfragment.methods.purchase_stars import purchase_stars
from pyfragment.methods.recharge_ads import recharge_ads
from pyfragment.methods.search_gifts import search_gifts
from pyfragment.methods.search_numbers import search_numbers
from pyfragment.methods.search_usernames import search_usernames
from pyfragment.methods.topup_ton import topup_ton
from pyfragment.types import (
    AdsRechargeResult,
    AdsTopupResult,
    ConfigurationError,
    CookieError,
    GiftsResult,
    LoginCodeResult,
    NumbersResult,
    PremiumGiveawayResult,
    PremiumResult,
    StarsGiveawayResult,
    StarsResult,
    TerminateSessionsResult,
    UsernamesResult,
    WalletInfo,
)
from pyfragment.types.constants import (
    DEFAULT_TIMEOUT,
    FRAGMENT_BASE_URL,
    REQUIRED_COOKIE_KEYS,
    SUPPORTED_WALLET_VERSIONS,
    WalletVersion,
)
from pyfragment.utils.http import fragment_request, get_fragment_hash, make_headers
from pyfragment.utils.wallet import get_wallet_info


class FragmentClient:
    """
    Client for the Fragment.com API.

    .. note::
        This library is not affiliated with, endorsed by, or in any way officially
        connected with Fragment or Telegram.

    Args:
        seed: 24-word mnemonic phrase for the TON wallet.
        api_key: Tonapi API key — get one at https://tonconsole.com.
        cookies: Fragment session cookies as a dict or JSON string.
        wallet_version: Wallet contract version — ``"V4R2"`` or ``"V5R1"`` (default).
        timeout: HTTP request timeout in seconds. Defaults to ``30.0``.

    Raises:
        ConfigurationError: If ``seed``, ``api_key``, or ``wallet_version`` are missing or invalid.
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
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        missing = [name for name, val in (("seed", seed), ("api_key", api_key)) if not val or not str(val).strip()]
        if missing:
            raise ConfigurationError(ConfigurationError.MISSING_VARS.format(keys=", ".join(missing)))

        word_count = len(seed.split())
        if word_count not in (12, 18, 24):
            raise ConfigurationError(ConfigurationError.INVALID_MNEMONIC.format(count=word_count))

        if len(api_key.strip()) < 68:
            raise ConfigurationError(ConfigurationError.INVALID_API_KEY.format(length=len(api_key.strip())))

        if isinstance(cookies, str):
            try:
                cookies = json.loads(cookies)
            except Exception as exc:
                raise CookieError(CookieError.READ_FAILED.format(exc=exc)) from exc

        missing_keys = [k for k in REQUIRED_COOKIE_KEYS if not str(cast(dict[str, Any], cookies).get(k, "")).strip()]
        if missing_keys:
            raise CookieError(CookieError.MISSING_KEYS.format(keys=", ".join(missing_keys)))

        version = wallet_version.strip().upper()
        if version not in SUPPORTED_WALLET_VERSIONS:
            raise ConfigurationError(
                ConfigurationError.UNSUPPORTED_VERSION.format(
                    version=version, supported=", ".join(sorted(SUPPORTED_WALLET_VERSIONS))
                )
            )

        self.seed: str = seed.strip()
        self.api_key: str = api_key.strip()
        self.cookies: dict[str, Any] = cast(dict[str, Any], cookies)
        self.wallet_version: WalletVersion = version  # type: ignore[assignment]
        self.timeout: float = timeout

    async def __aenter__(self) -> FragmentClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        pass

    def __repr__(self) -> str:
        return f"FragmentClient(wallet_version='{self.wallet_version}', cookies={len(self.cookies)} keys)"

    async def purchase_premium(self, username: str, months: int, show_sender: bool = True) -> PremiumResult:
        """Gift Telegram Premium to a user.

        Args:
            username: Recipient's Telegram username (with or without ``@``).
            months: Duration — ``3``, ``6``, or ``12``.
            show_sender: Show your name as the sender. Defaults to ``True``.

        Returns:
            :class:`PremiumResult` with ``transaction_id``, ``username``, and ``amount``.
        """
        return await purchase_premium(self, username, months, show_sender)

    async def purchase_stars(self, username: str, amount: int, show_sender: bool = True) -> StarsResult:
        """Send Telegram Stars to a user.

        Args:
            username: Recipient's Telegram username (with or without ``@``).
            amount: Number of stars — integer from ``50`` to ``1 000 000``.
            show_sender: Show your name as the gift sender. Defaults to ``True``.

        Returns:
            :class:`StarsResult` with ``transaction_id``, ``username``, and ``amount``.
        """
        return await purchase_stars(self, username, amount, show_sender)

    async def topup_ton(self, username: str, amount: int, show_sender: bool = True) -> AdsTopupResult:
        """Top up TON to a recipient's Telegram balance.

        Args:
            username: Recipient's Telegram username (with or without ``@``).
            amount: Amount in TON — integer from ``1`` to ``1 000 000 000``.
            show_sender: Show your name as the sender. Defaults to ``True``.

        Returns:
            :class:`AdsTopupResult` with ``transaction_id``, ``username``, and ``amount``.
        """
        return await topup_ton(self, username, amount, show_sender)

    async def recharge_ads(self, account: str, amount: int) -> AdsRechargeResult:
        """Add funds to your own Telegram Ads account.

        Args:
            account: Your Fragment Ads account identifier — the channel or bot username
                the Ads account is linked to (e.g. ``"@mychannel"``).
            amount: Amount in TON — integer from ``1`` to ``1 000 000 000``.

        Returns:
            :class:`AdsRechargeResult` with ``transaction_id`` and ``amount``.
        """
        return await recharge_ads(self, account, amount)

    async def get_wallet(self) -> WalletInfo:
        """Return the address, state and balance of the TON wallet.

        Returns:
            :class:`WalletInfo` with ``address`` (``"UQ..."``), ``state``
            (``"active"``, ``"uninit"``, ``"nonexist"``, or ``"frozen"``), and ``balance`` in TON.
        """
        return await get_wallet_info(self)

    async def giveaway_stars(
        self,
        channel: str,
        winners: int,
        amount: int,
    ) -> StarsGiveawayResult:
        """Run a Telegram Stars giveaway for a channel.

        Args:
            channel: Channel username (with or without ``@``).
            winners: Number of winners — integer from ``1`` to ``5``.
            amount: Stars each winner receives — integer from ``500`` to ``1 000 000``.

        Returns:
            :class:`StarsGiveawayResult` with ``transaction_id``, ``channel``,
            ``winners``, and ``amount``.
        """
        return await giveaway_stars(self, channel, winners, amount)

    async def giveaway_premium(
        self,
        channel: str,
        winners: int,
        months: int = 3,
    ) -> PremiumGiveawayResult:
        """Run a Telegram Premium giveaway for a channel.

        Args:
            channel: Channel username (with or without ``@``).
            winners: Number of winners — positive integer.
            months: Premium duration per winner — ``3``, ``6``, or ``12``. Defaults to ``3``.

        Returns:
            :class:`PremiumGiveawayResult` with ``transaction_id``, ``channel``,
            ``winners``, and ``amount``.
        """
        return await giveaway_premium(self, channel, winners, months)

    async def get_login_code(self, number: str) -> LoginCodeResult:
        """Fetch the current pending login code for an anonymous number.

        Args:
            number: Phone number with or without leading ``+`` (e.g. ``"+1234567890"``).

        Returns:
            :class:`LoginCodeResult` with ``number``, ``code`` (``None`` if none pending),
            and ``active_sessions`` count.
        """
        return await get_login_code(self, number)

    async def toggle_login_codes(self, number: str, can_receive: bool) -> None:
        """Enable or disable login code delivery for an anonymous number.

        Args:
            number: Phone number with or without leading ``+``.
            can_receive: ``True`` to allow receiving codes, ``False`` to block them.
        """
        return await toggle_login_codes(self, number, can_receive)

    async def terminate_sessions(self, number: str) -> TerminateSessionsResult:
        """Terminate all active Telegram sessions for an anonymous number.

        Args:
            number: Phone number with or without leading ``+``.

        Returns:
            :class:`TerminateSessionsResult` with ``number`` and ``message``.

        Raises:
            AnonymousNumberError: If the number is not owned by this account or has no active sessions.
        """
        return await terminate_sessions(self, number)

    async def search_usernames(
        self,
        query: str = "",
        sort: str | None = None,
        filter: str | None = None,
        offset_id: str | None = None,
    ) -> UsernamesResult:
        """Search the Fragment marketplace for Telegram usernames.

        Args:
            query: Search text (e.g. ``"durov"``). Omit or pass ``""`` to browse all.
            sort: Sort order — ``"price_desc"``, ``"price_asc"``, ``"listed"``, or
                ``"ending"``. Omit to use Fragment's default ordering.
            filter: Filter results — ``"auction"``, ``"sale"``, ``"sold"``, or
                ``""`` (available items). Omit to return all.
            offset_id: Pagination cursor — pass :attr:`UsernamesResult.next_offset_id`
                from a previous result to fetch the next page.

        Returns:
            :class:`UsernamesResult` with ``items`` (parsed list of item dicts)
            and ``next_offset_id`` (``None`` on the last page).
        """
        return await search_usernames(self, query, sort=sort, filter=filter, offset_id=offset_id)

    async def search_numbers(
        self,
        query: str = "",
        sort: str | None = None,
        filter: str | None = None,
        offset_id: str | None = None,
    ) -> NumbersResult:
        """Search the Fragment marketplace for anonymous Telegram numbers.

        Args:
            query: Search text (e.g. ``"888"``). Omit or pass ``""`` to browse all.
            sort: Sort order — ``"price_desc"``, ``"price_asc"``, ``"listed"``, or
                ``"ending"``. Omit to use Fragment's default ordering.
            filter: Filter results — ``"auction"``, ``"sale"``, ``"sold"``, or
                ``""`` (available items). Omit to return all.
            offset_id: Pagination cursor — pass :attr:`NumbersResult.next_offset_id`
                from a previous result to fetch the next page.

        Returns:
            :class:`NumbersResult` with ``items`` (parsed list of item dicts)
            and ``next_offset_id`` (``None`` on the last page).
        """
        return await search_numbers(self, query, sort=sort, filter=filter, offset_id=offset_id)

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
            query: Search text. Omit or pass ``""`` to browse without filtering by name.
            collection: Filter by gift collection slug (e.g. ``"artisanbrick"``). Omit for all.
            sort: Sort order — ``"price_desc"``, ``"price_asc"``, ``"listed"``, or
                ``"ending"``. Omit to use Fragment's default ordering.
            filter: Filter results — ``"auction"``, ``"sale"``, ``"sold"``, or
                ``""`` (available items). Omit to return all.
            view: Active attribute tab name (e.g. ``"Model"``, ``"Backdrop"``). Omit for default.
            attr: Attribute filters — mapping of trait name to accepted values, e.g.
                ``{"Model": ["Foosball"], "Backdrop": ["Celtic Blue", "Orange"]}``.
                Each key is sent as ``attr[Key]`` with its list of values.
            offset: Integer page offset from a previous :class:`GiftsResult`.
                Pass ``next_offset`` to fetch the next page.

        Returns:
            :class:`GiftsResult` with ``items`` (parsed list of item dicts)
            and ``next_offset`` (``None`` on the last page).
        """
        return await search_gifts(
            self, query, collection=collection, sort=sort, filter=filter, view=view, attr=attr, offset=offset
        )

    async def call(
        self, method: str, data: dict[str, Any] | None = None, *, page_url: str = FRAGMENT_BASE_URL
    ) -> dict[str, Any]:
        """Send a raw request to the Fragment API.

        Useful for accessing undocumented or future Fragment API methods
        without waiting for a library update.

        Args:
            method: Fragment API method name, e.g. ``"searchPremiumGiftRecipient"``.
            data: Additional form-data fields to include in the request body.
            page_url: Fragment page URL used to derive the API hash and headers.
                Defaults to ``FRAGMENT_BASE_URL`` (``"https://fragment.com"``).

        Returns:
            Raw parsed JSON response as a dict.

        Example::

            result = await client.call(
                "searchPremiumGiftRecipient",
                {"query": "@username", "months": 3},
                page_url="https://fragment.com/premium/gift",
            )
        """
        headers = make_headers(page_url)
        async with httpx.AsyncClient(cookies=self.cookies, timeout=self.timeout) as session:
            fragment_hash = await get_fragment_hash(self.cookies, headers, page_url, self.timeout)
            return await fragment_request(session, fragment_hash, headers, {"method": method, **(data or {})})
