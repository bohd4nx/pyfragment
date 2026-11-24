"""Transfer coordinators: the pending seqno, waiting for the previous message, and shared-coordinator failures."""

import asyncio
import itertools
import logging
import time
from collections.abc import Callable
from typing import Any

import pytest

from pyfragment import FragmentClient, LocalTransferCoordinator
from pyfragment.domains.wallet.transfers import process_transaction
from pyfragment.domains.wallet.transfers.queue import TransferQueue
from tests.domains.wallet.helpers import link, seqnos
from tests.support.fake_ton import FakeTon

MakeClient = Callable[..., FragmentClient]


class BrokenSave(LocalTransferCoordinator):
    async def save_pending(self, address: str, seqno: int, valid_until: float) -> None:
        raise ConnectionError("redis is down")


class TestLocalCoordinator:
    async def test_remembers_the_pending_seqno_per_wallet(self) -> None:
        coordinator = LocalTransferCoordinator()
        assert await coordinator.load_pending("wallet-a") is None
        await coordinator.save_pending("wallet-a", 7, 123.0)
        assert await coordinator.load_pending("wallet-a") == (7, 123.0)
        assert await coordinator.load_pending("wallet-b") is None

    def test_locks_each_wallet_on_its_own(self) -> None:
        coordinator = LocalTransferCoordinator()
        assert coordinator.lock("wallet-a") is coordinator.lock("wallet-a")
        assert coordinator.lock("wallet-a") is not coordinator.lock("wallet-b")

    async def test_clients_of_one_wallet_share_the_default(self, fake_ton: FakeTon, make_client: MakeClient) -> None:
        assert make_client().ton_wallet.coordinator is make_client().ton_wallet.coordinator


class TestNextSeqno:
    async def test_expired_pending_seqno_falls_back_to_the_chain(self, fake_ton: FakeTon, client: FragmentClient) -> None:
        fake_ton.seqno = 9
        await client.ton_wallet.coordinator.save_pending(client.ton_wallet.address, 3, time.time() - 1)
        assert await client.ton_wallet.next_seqno() == 9

    async def test_waits_for_the_pending_transfer_to_land(self, fake_ton: FakeTon, client: FragmentClient) -> None:
        fake_ton.seqno = 7  # message 7 was sent but is not in a block yet
        await client.ton_wallet.coordinator.save_pending(client.ton_wallet.address, 7, time.time() + 60)
        asyncio.get_running_loop().call_later(0.02, setattr, fake_ton, "seqno", 8)

        assert await client.ton_wallet.next_seqno() == 8
        assert fake_ton.seqno_reads > 1

    async def test_pending_transfer_that_expired_unlanded_no_longer_blocks(
        self, fake_ton: FakeTon, client: FragmentClient
    ) -> None:
        fake_ton.seqno = 7
        await client.ton_wallet.coordinator.save_pending(client.ton_wallet.address, 7, time.time() + 0.03)
        assert await client.ton_wallet.next_seqno() == 7

    async def test_the_later_of_the_local_and_the_shared_pending_wins(self, fake_ton: FakeTon, make_client: MakeClient) -> None:
        shared = LocalTransferCoordinator()
        client = make_client(transfer_coordinator=shared)
        address = client.ton_wallet.address
        await shared.save_pending(address, 9, time.time() + 60)
        fake_ton.seqno = 10  # past the shared pending seqno
        assert await client.ton_wallet.next_seqno() == 10

    async def test_long_wait_for_the_previous_transfer_is_logged_once(
        self, fake_ton: FakeTon, client: FragmentClient, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        monkeypatch.setattr("pyfragment.domains.wallet.wallet.LANDING_WARN_AFTER", 0.01)
        await client.ton_wallet.coordinator.save_pending(client.ton_wallet.address, 5, time.time() + 60)
        asyncio.get_running_loop().call_later(0.04, setattr, fake_ton, "seqno", 6)
        with caplog.at_level(logging.WARNING, logger="pyfragment"):
            await client.ton_wallet.next_seqno()
        assert caplog.text.count("The previous transfer has not landed yet") == 1

    async def test_highload_wallet_has_no_seqno(self, fake_ton: FakeTon, make_client: MakeClient) -> None:
        assert await make_client(wallet_version="HighloadV2").ton_wallet.next_seqno() is None
        assert fake_ton.seqno_reads == 0


class TestCustomCoordinator:
    async def test_is_used_instead_of_the_default(self, fake_ton: FakeTon, make_client: MakeClient) -> None:
        class Spy(LocalTransferCoordinator):
            locked = 0

            def lock(self, address: str) -> Any:
                self.locked += 1
                return super().lock(address)

        spy = Spy()
        client = make_client(transfer_coordinator=spy)
        await process_transaction(client, link())
        assert spy.locked == 1
        assert await spy.load_pending(client.ton_wallet.address) == (5, pytest.approx(time.time() + 60, abs=5))

    async def test_serves_several_wallets_with_their_own_pending_seqnos(
        self, fake_ton: FakeTon, make_client: MakeClient
    ) -> None:
        coordinator = LocalTransferCoordinator()
        client = make_client(transfer_coordinator=coordinator)
        await process_transaction(client, link())
        pending = await coordinator.load_pending(client.ton_wallet.address)
        assert pending is not None and pending[0] == 5
        assert await coordinator.load_pending("another-wallet") is None

    async def test_processes_sharing_it_never_reuse_a_seqno(
        self, fake_ton: FakeTon, make_client: MakeClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake_ton.seqno = 0
        queues = itertools.cycle([TransferQueue(), TransferQueue()])  # every other payment lands in the "other" process
        monkeypatch.setattr("pyfragment.domains.wallet.wallet.queue_for", lambda _: next(queues))
        client = make_client(transfer_coordinator=LocalTransferCoordinator())  # stands in for the Redis-backed one

        await asyncio.gather(*(process_transaction(client, link()) for _ in range(8)))

        assert seqnos(fake_ton) == list(range(8))

    async def test_a_pending_seqno_that_cannot_be_saved_does_not_fail_a_sent_payment(
        self, fake_ton: FakeTon, make_client: MakeClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.WARNING, logger="pyfragment"):
            intent = await process_transaction(make_client(transfer_coordinator=BrokenSave()), link())
        assert len(fake_ton.sent) == 1 and intent.msg_hash
        assert "Failed to save the pending seqno" in caplog.text

    async def test_the_next_message_waits_even_when_the_shared_coordinator_cannot_save(
        self, fake_ton: FakeTon, make_client: MakeClient
    ) -> None:
        fake_ton.landing_delay = 0.02
        client = make_client(transfer_coordinator=BrokenSave())
        client.ton_wallet.wallet()

        await asyncio.gather(*(process_transaction(client, link()) for _ in range(2)))

        assert seqnos(fake_ton) == [5, 6]
