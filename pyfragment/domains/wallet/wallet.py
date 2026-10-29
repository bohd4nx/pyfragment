"""The client's GRAM (ex TON) wallet: one blockchain API connection, and the key derived from the seed once."""

from __future__ import annotations

import asyncio
import base64
import time
from typing import TYPE_CHECKING, Any

import ton_core
from ton_core import (
    ContractState,
    NetworkGlobalID,
    WalletHighloadV2Params,
    WalletHighloadV3Params,
    WalletTgParams,
    WalletV4Params,
    WalletV5Params,
)
from tonutils.clients import TonapiClient, ToncenterClient
from tonutils.contracts.wallet import WalletHighloadV2, WalletHighloadV3R1, WalletTg, WalletV4R2, WalletV5R1
from tonutils.exceptions import ProviderResponseError

from pyfragment.constants import MAINNET_CHAIN_ID
from pyfragment.enums import ApiProvider, WalletVersion
from pyfragment.exceptions import ProviderError

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient

WALLET_CLASSES: dict[WalletVersion, Any] = {
    WalletVersion.V4R2: WalletV4R2,
    WalletVersion.V5R1: WalletV5R1,
    WalletVersion.HighloadV2: WalletHighloadV2,
    WalletVersion.HighloadV3R1: WalletHighloadV3R1,
    WalletVersion.TG: WalletTg,
}

# Transfer parameters of the wallets that order transfers by seqno; highload wallets tell them apart by query id.
SEQNO_PARAMS: dict[WalletVersion, Any] = {
    WalletVersion.V4R2: WalletV4Params,
    WalletVersion.V5R1: WalletV5Params,
    WalletVersion.TG: WalletTgParams,
}


def make_ton_client(client: FragmentClient) -> Any:
    if client.api_provider == ApiProvider.TONCENTER:
        return ToncenterClient(network=NetworkGlobalID.MAINNET, api_key=client.api_key)
    return TonapiClient(network=NetworkGlobalID.MAINNET, api_key=client.api_key)


def provider_error(template: str, exc: BaseException, **fields: object) -> ProviderError:
    status = exc.code if isinstance(exc, ProviderResponseError) else None
    return ProviderError(template.format(exc=exc, **fields), status)


class TonWallet:
    """The wallet behind a ``FragmentClient``, created on first use and reused until ``aclose()``.

    ``lock`` serializes signing and sending inside one process: two transfers built from the same seqno would make the
    wallet reject one of them. Processes sharing a seed must serialize their purchases themselves.
    """

    def __init__(self, client: FragmentClient) -> None:
        self._client = client
        self._ton: Any | None = None
        self._wallet: Any | None = None
        self._public_key: Any = None  # set together with _wallet
        self._account: dict[str, Any] | None = None
        self.lock = asyncio.Lock()

    @property
    def version(self) -> WalletVersion:
        return self._client.wallet_version

    def _provider(self) -> Any:
        if self._ton is None:
            self._ton = make_ton_client(self._client)
        return self._ton

    async def ton(self) -> Any:
        """The connected tonutils client."""
        ton = self._provider()
        if not ton.connected:
            await ton.connect()
        return ton

    def wallet(self) -> Any:
        """The tonutils wallet derived from the seed with the configured version and phrase scheme."""
        if self._wallet is None:
            self._wallet, self._public_key, _, _ = WALLET_CLASSES[self.version].from_mnemonic(
                client=self._provider(),
                mnemonic=self._client.seed,
                mnemonic_type=ton_core.MnemonicType(self._client.mnemonic_type.value),
            )
        return self._wallet

    def account_info(self) -> dict[str, Any]:
        """The TON Connect account payload Fragment needs to build a transaction for this wallet. No network involved."""
        if self._account is None:
            wallet = self.wallet()
            self._account = {
                "address": wallet.address.to_str(False, False),
                "publicKey": self._public_key.as_hex,
                "chain": MAINNET_CHAIN_ID,
                "walletStateInit": base64.b64encode(wallet.state_init.serialize().to_boc()).decode(),
            }
        return self._account

    async def state(self) -> Any:
        """The wallet's on-chain state (``balance`` in nanograms, ``state``).

        ``wallet.refresh()`` is deliberately not used: tonutils answers *any* provider failure (bad API key,
        outage, timeout) with an empty "nonexistent, zero balance" account, which would show up as an empty wallet.
        """
        ton = await self.ton()
        address = self.wallet().address
        return await ton.get_info(address)

    async def seqno(self, state: Any | None = None) -> int:
        """The seqno the next transfer has to carry: 0 until the wallet is deployed. Provider failures raise."""
        s = state if state is not None else await self.state()
        if s.state != ContractState.ACTIVE:
            return 0
        return int(await self.wallet().seqno())

    async def transfer_params(self, valid_until: int, state: Any | None = None) -> Any:
        """Transfer parameters that make the signed message expire at ``valid_until``, whatever the wallet kind.

        Seqno wallets also get an explicit seqno, read so that a provider failure raises instead of signing seqno 0.
        Pass ``state`` to reuse a previously fetched on-chain state and avoid a redundant provider call.
        """
        now = int(time.time())
        if self.version == WalletVersion.HighloadV2:
            return WalletHighloadV2Params(message_ttl=max(1, valid_until - now))
        if self.version == WalletVersion.HighloadV3R1:
            # A highload v3 message is accepted while created_at > now - timeout (and created_at <= now).
            return WalletHighloadV3Params(created_at=min(now, valid_until - self.wallet().config.timeout))
        try:
            seqno = await self.seqno(state)
        except Exception as exc:
            raise provider_error(ProviderError.WALLET_STATE_FAILED, exc) from exc
        return SEQNO_PARAMS[self.version](seqno=seqno, valid_until=valid_until)

    async def aclose(self) -> None:
        ton, self._ton = self._ton, None
        self._wallet = None
        if ton is not None and ton.connected:
            await ton.close()
