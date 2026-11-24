"""TransferQueue: grouping payments into messages, hooks, cancellation, and what a failed send means."""

import asyncio
import contextvars
import logging
import time
from collections.abc import Callable
from typing import Any

import pytest

from pyfragment import FragmentClient, LocalTransferCoordinator, ProviderError, TransactionError, TransferIntent
from pyfragment.domains.wallet.transfers import process_transaction
from pyfragment.domains.wallet.transfers.queue import Entry, drop_expired, queue_for
from pyfragment.domains.wallet.transfers.request import TransferRequest
from pyfragment.enums import PaymentMethod
from tests.domains.wallet.helpers import land, link, seqnos, sizes, until
from tests.support.fake_ton import FakeTon, provider_error

MakeClient = Callable[..., FragmentClient]


async def pay(client: FragmentClient, count: int, **options: Any) -> list[TransferIntent]:
    return list(await asyncio.gather(*(process_transaction(client, link(**options)) for _ in range(count))))


def start(client: FragmentClient) -> "asyncio.Future[TransferIntent]":
    return asyncio.ensure_future(process_transaction(client, link()))


class FakeTime:
    """Stands in for the ``time`` module of the queue: ``time.time()`` jumps ``offset`` seconds ahead."""

    def __init__(self, offset: float) -> None:
        self.offset = offset

    def time(self) -> float:
        return time.time() + self.offset


class TestGrouping:
    async def test_payments_go_one_per_message_by_default(self, fake_ton: FakeTon, make_client: MakeClient) -> None:
        await pay(make_client(), 6)
        assert sizes(fake_ton) == [1] * 6
        assert seqnos(fake_ton) == list(range(5, 11))
        assert len(fake_ton.landed) == 6

    async def test_queued_payments_go_out_together_up_to_max_batch(self, fake_ton: FakeTon, make_client: MakeClient) -> None:
        intents = await pay(make_client(max_batch=4), 10)
        assert sizes(fake_ton) == [4, 4, 2]
        assert seqnos(fake_ton) == [5, 6, 7]
        assert len({intent.msg_hash for intent in intents}) == 3  # payments of one group share a hash and a boc

    async def test_group_is_capped_by_what_the_wallet_can_carry(self, fake_ton: FakeTon, make_client: MakeClient) -> None:
        await pay(make_client(wallet_version="V4R2", max_batch=100), 9)
        assert sizes(fake_ton, "V4R2") == [4, 4, 1]

    async def test_lone_payment_is_not_held_back_for_company(self, fake_ton: FakeTon, make_client: MakeClient) -> None:
        await pay(make_client(max_batch=255), 1)
        assert sizes(fake_ton) == [1]

    async def test_clients_of_one_wallet_share_a_queue(self, fake_ton: FakeTon, make_client: MakeClient) -> None:
        clients = [make_client(max_batch=255) for _ in range(4)]
        await asyncio.gather(*(process_transaction(client, link()) for client in clients for _ in range(3)))
        assert sizes(fake_ton) == [12]

    async def test_clients_of_one_wallet_take_consecutive_seqnos(self, fake_ton: FakeTon, make_client: MakeClient) -> None:
        await asyncio.gather(pay(make_client(), 3), pay(make_client(), 3))
        assert seqnos(fake_ton) == list(range(5, 11))

    async def test_highload_wallet_batches_without_waiting_for_seqnos(self, fake_ton: FakeTon, make_client: MakeClient) -> None:
        await pay(make_client(wallet_version="HighloadV3R1", max_batch=50), 20)
        assert sizes(fake_ton, "HighloadV3R1") == [20]

    async def test_group_is_formed_after_the_previous_message_has_landed(
        self, fake_ton: FakeTon, make_client: MakeClient
    ) -> None:
        fake_ton.landing_delay = 3600
        client = make_client(max_batch=10)
        client.ton_wallet.wallet()  # deriving the key is slow
        first = start(client)
        await until(lambda: len(fake_ton.sent) == 1)
        others = [start(client) for _ in range(3)]
        await asyncio.sleep(0.01)

        land(fake_ton)
        await asyncio.gather(first, *others)

        assert sizes(fake_ton) == [1, 3]

    async def test_group_expires_with_its_earliest_invoice(self, fake_ton: FakeTon, make_client: MakeClient) -> None:
        client = make_client(max_batch=4)
        early, late, open_ended = await asyncio.gather(
            process_transaction(client, link(valid_for=30)),
            process_transaction(client, link(valid_for=300)),
            process_transaction(client, link(valid_for=None)),
        )
        assert early.valid_until == late.valid_until == open_ended.valid_until
        assert early.valid_until <= int(time.time()) + 30

    async def test_each_payment_gets_its_own_hook_call_with_the_shared_hash(
        self, fake_ton: FakeTon, make_client: MakeClient
    ) -> None:
        seen: list[TransferIntent] = []

        async def hook(intent: TransferIntent) -> None:
            seen.append(intent)

        intents = await pay(make_client(max_batch=4, on_transfer_prepared=hook), 3)
        assert seen == intents
        assert len({intent.msg_hash for intent in intents}) == 1

    async def test_finished_runner_is_not_kept_alive_by_its_queue(self, fake_ton: FakeTon, make_client: MakeClient) -> None:
        client = make_client()
        await pay(client, 2)
        assert queue_for(client.ton_wallet.address)._runner is None


class TestHooks:
    async def test_failing_hook_fails_only_its_own_payment(self, fake_ton: FakeTon, make_client: MakeClient) -> None:
        first_seen: list[TransferIntent] = []

        async def record(intent: TransferIntent) -> None:
            first_seen.append(intent)

        async def refuse(_: TransferIntent) -> None:
            raise RuntimeError("database is down")

        fine, failing = (
            make_client(max_batch=4, on_transfer_prepared=record),
            make_client(max_batch=4, on_transfer_prepared=refuse),
        )
        ok, bad = await asyncio.gather(
            process_transaction(fine, link()), process_transaction(failing, link()), return_exceptions=True
        )

        assert isinstance(ok, TransferIntent) and isinstance(bad, RuntimeError)
        assert len(fake_ton.sent) == 1
        # The message was signed again without the failed payment, and the hook of the other one saw its new intent.
        assert len(first_seen) == 2 and first_seen[0].msg_hash != first_seen[1].msg_hash
        assert ok.msg_hash == first_seen[-1].msg_hash

    async def test_group_whose_every_hook_fails_sends_nothing(self, fake_ton: FakeTon, make_client: MakeClient) -> None:
        async def refuse(_: TransferIntent) -> None:
            raise RuntimeError("database is down")

        with pytest.raises(RuntimeError):
            await process_transaction(make_client(on_transfer_prepared=refuse), link())
        assert fake_ton.sent == []

    async def test_hook_runs_in_the_context_of_its_own_caller(self, fake_ton: FakeTon, make_client: MakeClient) -> None:
        request_id: contextvars.ContextVar[str] = contextvars.ContextVar("request_id")
        seen: list[str] = []

        async def hook(_: TransferIntent) -> None:
            seen.append(request_id.get())

        client = make_client(max_batch=4, on_transfer_prepared=hook)

        async def purchase(name: str) -> TransferIntent:
            request_id.set(name)
            return await process_transaction(client, link())

        await asyncio.gather(purchase("first"), purchase("second"))
        assert sorted(seen) == ["first", "second"]

    async def test_slow_hooks_that_outlast_the_message_fail_it_as_retryable_without_sending(
        self, fake_ton: FakeTon, make_client: MakeClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        clock = FakeTime(0)

        async def slow_hook(_: TransferIntent) -> None:
            clock.offset += 1000

        monkeypatch.setattr("pyfragment.domains.wallet.transfers.queue.time", clock)
        with pytest.raises(TransactionError) as exc_info:
            await process_transaction(make_client(on_transfer_prepared=slow_hook), link())
        assert exc_info.value.retryable
        assert fake_ton.sent == []

    async def test_payment_whose_invoice_ran_out_while_queued_fails_as_retryable(
        self, fake_ton: FakeTon, make_client: MakeClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("pyfragment.domains.wallet.transfers.queue.time", FakeTime(1000))
        with pytest.raises(TransactionError) as exc_info:
            await process_transaction(make_client(), link())
        assert exc_info.value.retryable
        assert fake_ton.sent == []


class TestCancellation:
    async def test_cancelled_payment_does_not_hold_up_the_others(self, fake_ton: FakeTon, make_client: MakeClient) -> None:
        client = make_client(max_batch=4)
        tasks = [start(client) for _ in range(3)]
        await asyncio.sleep(0)
        tasks[1].cancel()

        results = await asyncio.gather(*tasks, return_exceptions=True)

        assert isinstance(results[1], asyncio.CancelledError)
        assert isinstance(results[0], TransferIntent) and isinstance(results[2], TransferIntent)
        assert sizes(fake_ton) == [2]

    async def test_payment_cancelled_before_the_runner_starts_is_never_signed(
        self, fake_ton: FakeTon, make_client: MakeClient
    ) -> None:
        caller = start(make_client())
        await asyncio.sleep(0)
        caller.cancel()
        await asyncio.gather(caller, return_exceptions=True)
        await asyncio.sleep(0.01)
        assert fake_ton.sent == []

    async def test_payment_cancelled_while_waiting_for_the_previous_block_is_never_sent(
        self, fake_ton: FakeTon, make_client: MakeClient
    ) -> None:
        fake_ton.landing_delay = 3600
        client = make_client(max_batch=10)
        client.ton_wallet.wallet()
        first = start(client)
        await until(lambda: len(fake_ton.sent) == 1)
        second = start(client)
        await asyncio.sleep(0.01)
        second.cancel()
        land(fake_ton)

        results = await asyncio.gather(first, second, return_exceptions=True)

        assert isinstance(results[0], TransferIntent)
        assert isinstance(results[1], asyncio.CancelledError)
        assert len(fake_ton.sent) == 1

    async def test_nothing_is_sent_when_every_caller_is_cancelled_while_the_hooks_run(
        self, fake_ton: FakeTon, make_client: MakeClient
    ) -> None:
        callers: list[asyncio.Future[Any]] = []

        async def cancel_the_callers(_: TransferIntent) -> None:
            for caller in callers:
                caller.cancel()
            await asyncio.sleep(0)
            await asyncio.sleep(0)

        callers.append(start(make_client(on_transfer_prepared=cancel_the_callers)))
        results = await asyncio.gather(*callers, return_exceptions=True)
        assert isinstance(results[0], asyncio.CancelledError)
        assert fake_ton.sent == []

    async def test_payment_sent_after_its_caller_was_cancelled_is_logged(
        self, fake_ton: FakeTon, make_client: MakeClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        doomed: list[asyncio.Future[Any]] = []

        async def cancel_one(_: TransferIntent) -> None:
            doomed[0].cancel()
            await asyncio.sleep(0)
            await asyncio.sleep(0)

        client = make_client(max_batch=4, on_transfer_prepared=cancel_one)
        with caplog.at_level(logging.WARNING, logger="pyfragment"):
            doomed.append(start(client))
            survivor = start(client)
            await asyncio.gather(*doomed, survivor, return_exceptions=True)

        assert len(fake_ton.sent) == 1
        assert "Payment sent after its caller was cancelled (msg_hash=" in caplog.text

    async def test_hook_that_is_cancelled_cancels_only_its_own_payment(
        self, fake_ton: FakeTon, make_client: MakeClient
    ) -> None:
        async def cancelled_hook(_: TransferIntent) -> None:
            raise asyncio.CancelledError

        fine, odd = make_client(max_batch=4), make_client(max_batch=4, on_transfer_prepared=cancelled_hook)
        ok, cancelled = await asyncio.gather(
            process_transaction(fine, link()), process_transaction(odd, link()), return_exceptions=True
        )
        assert isinstance(ok, TransferIntent)
        assert isinstance(cancelled, asyncio.CancelledError)
        assert len(fake_ton.sent) == 1

    @pytest.mark.parametrize("max_batch", [1, 4])
    async def test_cancelling_hooks_leave_no_caller_hanging(
        self, fake_ton: FakeTon, make_client: MakeClient, max_batch: int
    ) -> None:
        async def cancelled_hook(_: TransferIntent) -> None:
            raise asyncio.CancelledError

        client = make_client(max_batch=max_batch, on_transfer_prepared=cancelled_hook)
        results = await asyncio.wait_for(
            asyncio.gather(*(process_transaction(client, link()) for _ in range(3)), return_exceptions=True), timeout=2
        )
        assert all(isinstance(result, asyncio.CancelledError) for result in results)
        assert fake_ton.sent == []

    async def test_cancelling_the_runner_settles_everyone_still_waiting(
        self, fake_ton: FakeTon, make_client: MakeClient
    ) -> None:
        fake_ton.landing_delay = 3600
        client = make_client(max_batch=1)
        client.ton_wallet.wallet()
        first = start(client)
        await until(lambda: len(fake_ton.sent) == 1)
        waiting = [start(client) for _ in range(2)]
        await asyncio.sleep(0.01)
        runner = queue_for(client.ton_wallet.address)._runner
        assert runner is not None

        runner.cancel()
        results = await asyncio.wait_for(asyncio.gather(first, *waiting, return_exceptions=True), timeout=2)

        assert isinstance(results[0], TransferIntent)
        assert all(isinstance(result, asyncio.CancelledError) for result in results[1:])

    async def test_runner_cancelled_while_a_hook_runs_cancels_the_group_and_the_queue(
        self, fake_ton: FakeTon, make_client: MakeClient
    ) -> None:
        started = asyncio.Event()

        async def slow_hook(_: TransferIntent) -> None:
            started.set()
            await asyncio.sleep(10)

        client = make_client(max_batch=1, on_transfer_prepared=slow_hook)
        callers = [start(client) for _ in range(2)]
        await asyncio.wait_for(started.wait(), timeout=2)
        runner = queue_for(client.ton_wallet.address)._runner
        assert runner is not None

        runner.cancel()
        results = await asyncio.wait_for(asyncio.gather(*callers, return_exceptions=True), timeout=2)

        assert all(isinstance(result, asyncio.CancelledError) for result in results)
        assert fake_ton.sent == []


class TestSending:
    async def test_error_on_a_send_that_landed_is_a_success(self, fake_ton: FakeTon, client: FragmentClient) -> None:
        # toncenter answers 500 to some sends that went through.
        fake_ton.send_errors = [(provider_error(500, "internal"), True)]
        sent = await process_transaction(client, link())
        assert len(fake_ton.sent) == 1 and len(fake_ton.landed) == 1 and fake_ton.seqno == 6
        assert sent.comment

    @pytest.mark.parametrize("code", [400, 401, 404])
    async def test_definite_rejection_is_a_non_retryable_provider_error(
        self, fake_ton: FakeTon, client: FragmentClient, code: int
    ) -> None:
        fake_ton.send_errors = [(provider_error(code, "rejected"), False)]
        with pytest.raises(ProviderError, match=str(code)) as exc_info:
            await process_transaction(client, link())
        assert not exc_info.value.retryable and exc_info.value.status == code
        assert fake_ton.landed == []

    @pytest.mark.parametrize(
        "error",
        [provider_error(429), provider_error(502), RuntimeError("connection reset")],
        ids=["rate-limit", "5xx", "network"],
    )
    async def test_ambiguous_send_error_is_logged_and_the_intent_returned(
        self, fake_ton: FakeTon, client: FragmentClient, caplog: pytest.LogCaptureFixture, error: Exception
    ) -> None:
        fake_ton.send_errors = [(error, False)]
        with caplog.at_level(logging.WARNING, logger="pyfragment"):
            sent = await process_transaction(client, link())
        assert "Failed to send transfer" in caplog.text
        assert isinstance(sent, TransferIntent)

    async def test_a_provider_failure_while_signing_is_a_provider_error(
        self, fake_ton: FakeTon, client: FragmentClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def fail(*_: object, **__: object) -> None:
            raise provider_error(500)

        monkeypatch.setattr("tonutils.contracts.wallet.WalletV5R1.build_external_message", fail)
        with pytest.raises(ProviderError):
            await process_transaction(client, link())
        assert fake_ton.sent == []


class TestDropExpired:
    async def test_expired_entries_fail_as_retryable_and_the_rest_stay(self) -> None:
        def entry(deadline: int | None) -> Entry:
            request = TransferRequest(
                builder=None,  # type: ignore[arg-type]
                destination="0:abc",
                amount_nano=1,
                comment=None,
                payment_method=PaymentMethod.GRAM,
                req_id=None,
                deadline=deadline,
                on_prepared=None,
            )
            return Entry(request, wallet=None, done=asyncio.get_running_loop().create_future())  # type: ignore[arg-type]

        expired, open_ended = entry(int(time.time()) - 1), entry(None)
        assert drop_expired([expired, open_ended]) == [open_ended]
        error = expired.done.exception()
        assert isinstance(error, TransactionError) and error.retryable


class TestLockFailures:
    async def test_failing_release_does_not_fail_a_group_that_was_never_tried(
        self, fake_ton: FakeTon, make_client: MakeClient
    ) -> None:
        class FailsToRelease:
            async def __aenter__(self) -> None:
                return None

            async def __aexit__(self, *_: object) -> None:
                raise ConnectionError("redis is down")

        class Coordinator(LocalTransferCoordinator):
            def lock(self, address: str) -> Any:
                return FailsToRelease()

        callers: list[asyncio.Future[Any]] = []
        hooks_run = 0

        async def cancel_the_first(_: TransferIntent) -> None:
            nonlocal hooks_run
            hooks_run += 1
            if hooks_run == 1:
                callers[0].cancel()
                await asyncio.sleep(0)
                await asyncio.sleep(0)

        client = make_client(max_batch=1, transfer_coordinator=Coordinator(), on_transfer_prepared=cancel_the_first)
        callers.extend([start(client), start(client)])
        results = await asyncio.wait_for(asyncio.gather(*callers, return_exceptions=True), timeout=2)

        assert isinstance(results[0], asyncio.CancelledError)
        assert isinstance(results[1], TransferIntent)
        assert len(fake_ton.sent) == 1

    async def test_failing_release_after_the_send_still_delivers_the_intent(
        self, fake_ton: FakeTon, make_client: MakeClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        class FailsToRelease:
            async def __aenter__(self) -> None:
                return None

            async def __aexit__(self, *_: object) -> None:
                raise ConnectionError("redis is down")

        class Coordinator(LocalTransferCoordinator):
            def lock(self, address: str) -> Any:
                return FailsToRelease()

        with caplog.at_level(logging.WARNING, logger="pyfragment"):
            sent = await process_transaction(make_client(transfer_coordinator=Coordinator()), link())
        assert isinstance(sent, TransferIntent) and len(fake_ton.sent) == 1
        assert "Failed to release the transfer lock after sending" in caplog.text

    async def test_cancelled_release_still_delivers_the_sent_payment(self, fake_ton: FakeTon, make_client: MakeClient) -> None:
        class CancelledOnRelease:
            async def __aenter__(self) -> None:
                return None

            async def __aexit__(self, *_: object) -> None:
                raise asyncio.CancelledError

        class Coordinator(LocalTransferCoordinator):
            def lock(self, address: str) -> Any:
                return CancelledOnRelease()

        result = (
            await asyncio.gather(
                process_transaction(make_client(transfer_coordinator=Coordinator()), link()), return_exceptions=True
            )
        )[0]
        assert isinstance(result, TransferIntent)
        assert len(fake_ton.sent) == 1
