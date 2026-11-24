"""TonWallet: the provider connection, the account Fragment is told about, and wallet state."""

from collections.abc import Callable
from unittest.mock import MagicMock

import pytest
from ton_core import ContractState
from tonutils.types import DEFAULT_HTTP_RETRY_POLICY

from pyfragment import FragmentClient, ProviderError
from pyfragment.domains.wallet.wallet import WALLET_CLASSES, make_ton_client
from pyfragment.enums import ApiProvider, WalletVersion
from tests.support.data import API_KEY, BIP39_SEED_12_WORDS, COOKIES, SEED
from tests.support.fake_ton import FakeTon


def seed_for(version: WalletVersion) -> str:
    return BIP39_SEED_12_WORDS if version == WalletVersion.TG else SEED


class TestMakeTonClient:
    @pytest.mark.parametrize(
        ("provider", "client_class"), [(ApiProvider.TONCENTER, "ToncenterClient"), (ApiProvider.TONAPI, "TonapiClient")]
    )
    def test_provider_selects_the_client_class_and_retry_policy(
        self, monkeypatch: pytest.MonkeyPatch, provider: ApiProvider, client_class: str
    ) -> None:
        built = MagicMock()
        monkeypatch.setattr(f"pyfragment.domains.wallet.wallet.{client_class}", built)
        make_ton_client(FragmentClient(api_provider=provider, seed=SEED, api_key=API_KEY, cookies=COOKIES))
        # Rate limits and transient errors are retried by tonutils itself.
        assert built.call_args.kwargs["retry_policy"] is DEFAULT_HTTP_RETRY_POLICY


class TestConnection:
    async def test_is_made_once_and_closed_with_the_client(self, fake_ton: FakeTon) -> None:
        async with FragmentClient(seed=SEED, api_key=API_KEY, cookies=COOKIES) as client:
            await client.ton_wallet.state()
            await client.ton_wallet.state()
            assert fake_ton.connected
        assert fake_ton.closed and not fake_ton.connected

    async def test_state_surfaces_provider_failures(self, fake_ton: FakeTon, client: FragmentClient) -> None:
        fake_ton.info_errors = [RuntimeError("down")]
        with pytest.raises(RuntimeError, match="down"):
            await client.ton_wallet.state()


class TestAccountInfo:
    def test_needs_no_network_and_is_cached(self, fake_ton: FakeTon, client: FragmentClient) -> None:
        account = client.ton_wallet.account_info()
        assert client.ton_wallet.account_info() is account
        assert not fake_ton.connected
        assert account["address"] == client.ton_wallet.wallet().address.to_str(False, False)
        assert account["chain"] == "-239"
        assert account["walletStateInit"]

    @pytest.mark.parametrize("version", list(WalletVersion))
    def test_every_wallet_version_has_its_own_address(
        self, make_client: Callable[..., FragmentClient], version: WalletVersion
    ) -> None:
        wallet = make_client(wallet_version=version.value, seed=seed_for(version)).ton_wallet
        assert isinstance(wallet.wallet(), WALLET_CLASSES[version])
        assert wallet.address == wallet.account_info()["address"]

    def test_wallet_versions_derive_different_addresses(self, make_client: Callable[..., FragmentClient]) -> None:
        addresses = {make_client(wallet_version=v.value, seed=seed_for(v)).ton_wallet.address for v in WalletVersion}
        assert len(addresses) == len(WalletVersion)


class TestBatchLimit:
    @pytest.mark.parametrize(
        ("version", "max_batch", "expected"),
        [("V5R1", 1, 1), ("V5R1", 100, 100), ("V4R2", 100, 4), ("V4R2", 2, 2)],
    )
    def test_is_max_batch_capped_by_the_wallet(
        self, make_client: Callable[..., FragmentClient], version: str, max_batch: int, expected: int
    ) -> None:
        assert make_client(wallet_version=version, max_batch=max_batch).ton_wallet.batch_limit == expected


class TestSeqno:
    async def test_undeployed_wallet_is_seqno_zero_without_asking_the_contract(
        self, fake_ton: FakeTon, client: FragmentClient
    ) -> None:
        fake_ton.state, fake_ton.seqno = ContractState.UNINIT, 3
        assert await client.ton_wallet.seqno() == 0
        assert fake_ton.seqno_reads == 0

    async def test_deployed_wallet_is_not_asked_for_its_state_again(self, fake_ton: FakeTon, client: FragmentClient) -> None:
        assert await client.ton_wallet.seqno() == 5
        fake_ton.state = ContractState.UNINIT  # a deployed wallet never goes back
        assert await client.ton_wallet.seqno() == 5

    async def test_next_seqno_wraps_a_read_failure(self, fake_ton: FakeTon, client: FragmentClient) -> None:
        fake_ton.seqno_errors = [RuntimeError("down")]
        with pytest.raises(ProviderError, match="down"):
            await client.ton_wallet.next_seqno()
