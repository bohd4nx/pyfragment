import json

from pyfragment.methods.premium import purchase_premium
from pyfragment.methods.stars import purchase_stars
from pyfragment.methods.ton import topup_ton
from pyfragment.types import (
    REQUIRED_COOKIE_KEYS,
    SUPPORTED_WALLET_VERSIONS,
    AdsTopupResult,
    ConfigurationError,
    CookieError,
    PremiumResult,
    StarsResult,
    WalletInfo,
    WalletVersion,
)
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

    Raises:
        ConfigurationError: If ``seed``, ``api_key``, or ``wallet_version`` are missing or invalid.
        CookieError: If ``cookies`` cannot be parsed or are missing required keys.

    Example::

        client = FragmentClient(
            seed="word1 word2 ...",
            api_key="AAABBB...",
            cookies={"stel_ssid": "...", "stel_dt": "...", ...},
        )
        print(await client.get_wallet())
        result = await client.purchase_premium("@username", months=6)
        print(result.transaction_id)
    """

    def __init__(
        self,
        seed: str,
        api_key: str,
        cookies: dict | str,
        wallet_version: str = "V5R1",
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

        missing_keys = [k for k in REQUIRED_COOKIE_KEYS if not str(cookies.get(k, "")).strip()]
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
        self.cookies: dict = cookies
        self.wallet_version: WalletVersion = version  # type: ignore[assignment]

    async def purchase_premium(self, username: str, months: int, show_sender: bool = True) -> PremiumResult:
        """Purchase Telegram Premium for a user.

        Args:
            username: Recipient's Telegram username (with or without ``@``).
            months: Duration — ``3``, ``6``, or ``12``.
            show_sender: Show your name as the sender. Defaults to ``True``.

        Returns:
            :class:`PremiumResult` with ``transaction_id``, ``username``, ``months``, ``timestamp``.
        """
        return await purchase_premium(self, username, months, show_sender)

    async def purchase_stars(self, username: str, amount: int, show_sender: bool = True) -> StarsResult:
        """Purchase Telegram Stars for a user.

        Args:
            username: Recipient's Telegram username (with or without ``@``).
            amount: Number of stars — integer from ``50`` to ``1 000 000``.
            show_sender: Show your name as the gift sender. Defaults to ``True``.

        Returns:
            :class:`StarsResult` with ``transaction_id``, ``username``, ``stars``, ``timestamp``.
        """
        return await purchase_stars(self, username, amount, show_sender)

    async def topup_ton(self, username: str, amount: int, show_sender: bool = True) -> AdsTopupResult:
        """Top up Telegram Ads balance with TON.

        Args:
            username: Ads account username (with or without ``@``).
            amount: Amount in TON — integer from ``1`` to ``1 000 000 000``.
            show_sender: Show your name as the sender. Defaults to ``True``.

        Returns:
            :class:`AdsTopupResult` with ``transaction_id``, ``username``, ``amount``, ``timestamp``.
        """
        return await topup_ton(self, username, amount, show_sender)

    async def get_wallet(self) -> WalletInfo:
        """Return the address, state and balance of the TON wallet.

        Returns:
            :class:`WalletInfo` with ``address`` (``"UQ..."``), ``state``
            (``"active"``, ``"uninit"``, or ``"frozen"``), and ``balance`` in TON.
        """
        return await get_wallet_info(self)
