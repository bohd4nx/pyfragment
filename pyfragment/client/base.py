from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from pyfragment.constants import (
    BASE_HEADERS,
    CONFIRM_STATE_TIMEOUT,
    DEFAULT_MAX_BATCH,
    DEFAULT_TIMEOUT,
    FRAGMENT_BASE_URL,
)
from pyfragment.domains.wallet.models import TransferIntent
from pyfragment.domains.wallet.transfers import TransferCoordinator
from pyfragment.domains.wallet.wallet import TonWallet
from pyfragment.enums import ApiMethod, ApiProvider, MnemonicType, WalletVersion
from pyfragment.transport import FragmentTransport
from pyfragment.utils.validation import (
    normalize_confirm_timeout,
    normalize_max_batch,
    normalize_mnemonic_type,
    normalize_provider,
    normalize_wallet_version,
    parse_cookies,
    validate_cookie_keys,
    validate_credentials,
    validate_seed,
)

_T = TypeVar("_T", bound="BaseClient")


class BaseClient:
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
        confirm_timeout: float = CONFIRM_STATE_TIMEOUT,
        on_transfer_prepared: Callable[[TransferIntent], Awaitable[None]] | None = None,
        transfer_coordinator: TransferCoordinator | None = None,
        max_batch: int = DEFAULT_MAX_BATCH,
    ) -> None:
        validate_credentials(seed, api_key)
        provider = normalize_provider(api_provider)
        parsed_cookies = parse_cookies(cookies)
        validate_cookie_keys(parsed_cookies)
        version = normalize_wallet_version(wallet_version)
        phrase_type = normalize_mnemonic_type(mnemonic_type, version)
        validate_seed(seed, version, phrase_type)

        self.seed: str = seed
        self.api_key: str = api_key.strip()
        self.api_provider: ApiProvider = provider
        self.cookies: dict[str, Any] = parsed_cookies
        self.wallet_version: WalletVersion = version
        self.mnemonic_type: MnemonicType = phrase_type
        self.timeout: float = timeout
        self.headers: dict[str, str | None] = dict(headers) if headers is not None else dict(BASE_HEADERS)
        self.confirm_timeout: float = normalize_confirm_timeout(confirm_timeout)
        self.on_transfer_prepared: Callable[[TransferIntent], Awaitable[None]] | None = on_transfer_prepared
        self.transfer_coordinator: TransferCoordinator | None = transfer_coordinator
        self.max_batch: int = normalize_max_batch(max_batch)
        self._transport = FragmentTransport(parsed_cookies, timeout, self.headers)
        self.ton_wallet = TonWallet(self)

    async def __aenter__(self: _T) -> _T:
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
