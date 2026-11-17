from __future__ import annotations

import asyncio
import base64
import time
from typing import TYPE_CHECKING, Any

import tonutils.exceptions
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
from tonutils.types import DEFAULT_HTTP_RETRY_POLICY

from pyfragment.constants import MAINNET_CHAIN_ID, SEQNO_POLL_INTERVAL
from pyfragment.domains.wallet.models import TransferIntent
from pyfragment.domains.wallet.transfers.coordinator import TransferCoordinator
from pyfragment.domains.wallet.transfers.queue import queue_for
from pyfragment.enums import ApiProvider, WalletVersion
from pyfragment.exceptions import ProviderError

if TYPE_CHECKING:
    from pyfragment.client.base import BaseClient
    from pyfragment.domains.wallet.transfers.request import TransferRequest

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


def make_ton_client(client: BaseClient) -> Any:
    provider = ToncenterClient if client.api_provider == ApiProvider.TONCENTER else TonapiClient
    return provider(network=NetworkGlobalID.MAINNET, api_key=client.api_key, retry_policy=DEFAULT_HTTP_RETRY_POLICY)


class TonWallet:
    """The wallet behind a ``FragmentClient``, created on first use and reused until ``aclose()``.

    Transfers go through a per-wallet queue that sends them in groups (see ``TransferQueue``). ``coordinator``
    serializes the groups: two messages built from the same seqno would make the wallet reject one of them. The
    default only covers one process; processes sharing a seed pass a shared ``TransferCoordinator`` to the client.
    """

    def __init__(self, client: BaseClient) -> None:
        self._client = client
        self._ton: Any | None = None
        self._wallet: Any | None = None
        self._public_key: Any = None  # set together with _wallet
        self._account: dict[str, Any] | None = None

    @property
    def version(self) -> WalletVersion:
        return self._client.wallet_version

    @property
    def address(self) -> str:
        return str(self.wallet().address.to_str(False, False))

    @property
    def coordinator(self) -> TransferCoordinator:
        return self._client.transfer_coordinator or queue_for(self.address).coordinator

    @property
    def batch_limit(self) -> int:
        """Transfers sent in one message: ``FragmentClient(max_batch=...)``, capped by what the wallet can carry."""
        return min(self._client.max_batch, int(self.wallet().MAX_MESSAGES))

    def _provider(self) -> Any:
        if self._ton is None:
            self._ton = make_ton_client(self._client)
        return self._ton

    async def ton(self) -> Any:
        ton = self._provider()
        if not ton.connected:
            await ton.connect()
        return ton

    def wallet(self) -> Any:
        if self._wallet is None:
            self._wallet, self._public_key, _, _ = WALLET_CLASSES[self.version].from_mnemonic(
                client=self._provider(),
                mnemonic=self._client.seed,
                mnemonic_type=self._client.mnemonic_type,
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

    async def seqno(self) -> int:
        if (await self.state()).state != ContractState.ACTIVE:
            return 0
        return int(await self.wallet().seqno())

    async def transfer_params(self, valid_until: int) -> Any:
        now = int(time.time())
        if self.version == WalletVersion.HighloadV2:
            return WalletHighloadV2Params(message_ttl=max(1, valid_until - now))
        if self.version == WalletVersion.HighloadV3R1:
            # A highload v3 message is accepted while created_at > now - timeout (and created_at <= now).
            return WalletHighloadV3Params(created_at=min(now, valid_until - self.wallet().config.timeout))
        return SEQNO_PARAMS[self.version](seqno=await self.next_seqno(), valid_until=valid_until)

    async def next_seqno(self) -> int:
        """The chain's seqno once the previous message has landed or expired.

        A node rejects a message whose seqno is ahead of the chain, so the seqno can't be counted on from a pending
        message: its landing is waited for.
        """
        pending = await self.coordinator.load_pending()
        while True:
            try:
                seqno = await self.seqno()
            except Exception as exc:
                raise ProviderError.from_exception(ProviderError.WALLET_STATE_FAILED, exc) from exc
            if pending is None or seqno > pending[0] or time.time() >= pending[1]:
                return seqno
            await asyncio.sleep(SEQNO_POLL_INTERVAL)

    async def transfer(self, request: TransferRequest) -> TransferIntent:
        return await queue_for(self.address).submit(self, request)

    async def sign(self, builders: list[Any], params: Any) -> Any:
        try:
            return await self.wallet().build_external_message(builders, params)
        except tonutils.exceptions.ProviderError as exc:
            raise ProviderError.from_exception(ProviderError.WALLET_STATE_FAILED, exc) from exc

    async def commit_seqno(self, params: Any, valid_until: int) -> None:
        """Record that a message with params.seqno was sent; prevents seqno reuse until valid_until passes."""
        if self.version in SEQNO_PARAMS:
            await self.coordinator.save_pending(params.seqno, float(valid_until))

    async def aclose(self) -> None:
        ton, self._ton = self._ton, None
        self._wallet = None
        self._account = None
        if ton is not None and ton.connected:
            await ton.close()
