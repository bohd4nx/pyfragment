"""Payments of one wallet are queued and sent in groups: one external message and one seqno each."""

import asyncio
import itertools
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import patch

import pytest

from pyfragment import (
    FragmentClient,
    LocalTransferCoordinator,
    TransactionError,
    TransferIntent,
)
from pyfragment.domains.wallet.transfers import process_transaction
from pyfragment.domains.wallet.transfers.queue import Entry, TransferQueue, drop_expired
from pyfragment.domains.wallet.transfers.request import TransferRequest
from pyfragment.domains.wallet.wallet import TonWallet
from pyfragment.enums import PaymentMethod
from tests.fake_ton import FakeTon, use_fake_ton
from tests.shared import VALID_API_KEY, VALID_COOKIES, VALID_SEED, fixture_json

STARS_NANO = 460_900_000  # what the recorded Stars invoice asks for


def stars_link(valid_for: int | None = 300) -> dict[str, Any]:
    link = fixture_json("stars_transaction_link_response.json")
    if valid_for is None:
        del link["transaction"]["validUntil"]
    else:
        link["transaction"]["validUntil"] = int(time.time()) + valid_for
    return link


def new_client(**options: Any) -> FragmentClient:
    return FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES, **options)


class Messages:
    """How many payments each signed external message carried, and the seqnos they were signed with."""

    def __init__(self) -> None:
        self.sizes: list[int] = []
        self.seqnos: list[int | None] = []


@asynccontextmanager
async def recording() -> AsyncIterator[Messages]:
    messages = Messages()
    sign, transfer_params = TonWallet.sign, TonWallet.transfer_params

    async def counting_sign(self: TonWallet, builders: list[Any], params: Any) -> Any:
        messages.sizes.append(len(builders))
        return await sign(self, builders, params)

    async def recording_params(self: TonWallet, valid_until: int) -> Any:
        params = await transfer_params(self, valid_until)
        messages.seqnos.append(getattr(params, "seqno", None))
        return params

    with patch.object(TonWallet, "sign", counting_sign), patch.object(TonWallet, "transfer_params", recording_params):
        yield messages


async def pay(client: FragmentClient, count: int, **link: Any) -> list[TransferIntent]:
    return list(await asyncio.gather(*(process_transaction(client, stars_link(**link)) for _ in range(count))))


@pytest.mark.asyncio
async def test_payments_are_sent_one_per_message_by_default() -> None:
    ton = FakeTon(seqno=5)
    with use_fake_ton(ton):
        async with new_client() as client, recording() as messages:
            await pay(client, 10)
    assert messages.sizes == [1] * 10
    assert messages.seqnos == list(range(5, 15))
    assert len(ton.landed) == 10


@pytest.mark.asyncio
async def test_several_clients_on_one_wallet_still_take_consecutive_seqnos() -> None:
    ton = FakeTon(seqno=5)
    with use_fake_ton(ton):
        first, second = new_client(), new_client()
        try:
            async with recording() as messages:
                await asyncio.gather(pay(first, 3), pay(second, 3))
        finally:
            await asyncio.gather(first.aclose(), second.aclose())
    assert messages.seqnos == list(range(5, 11))


@pytest.mark.asyncio
async def test_queued_payments_go_out_together_up_to_max_batch() -> None:
    ton = FakeTon(seqno=5)
    with use_fake_ton(ton):
        async with new_client(max_batch=4) as client, recording() as messages:
            intents = await pay(client, 10)
    assert messages.sizes == [4, 4, 2]
    assert messages.seqnos == [5, 6, 7]
    assert len(ton.landed) == 3
    assert len({intent.msg_hash for intent in intents}) == 3  # payments of one group share a hash and a boc


@pytest.mark.asyncio
async def test_queues_of_two_processes_sharing_a_coordinator_never_reuse_a_seqno() -> None:
    ton = FakeTon(seqno=0)
    coordinator = LocalTransferCoordinator()  # stands in for the Redis-backed one shared by the processes
    queues = itertools.cycle([TransferQueue(), TransferQueue()])  # every other payment lands in the "other" process
    with use_fake_ton(ton), patch("pyfragment.domains.wallet.wallet.queue_for", lambda _: next(queues)):
        async with new_client(transfer_coordinator=coordinator) as client, recording() as messages:
            await pay(client, 10)
    assert messages.seqnos == list(range(10))


@pytest.mark.asyncio
async def test_a_lone_payment_is_not_held_back_for_company() -> None:
    ton = FakeTon()
    with use_fake_ton(ton):
        async with new_client(max_batch=255) as client, recording() as messages:
            await pay(client, 1)
    assert messages.sizes == [1]


@pytest.mark.asyncio
async def test_clients_of_one_wallet_share_a_queue() -> None:
    ton = FakeTon()
    with use_fake_ton(ton):
        clients = [new_client(max_batch=255) for _ in range(4)]
        try:
            async with recording() as messages:
                await asyncio.gather(*(process_transaction(client, stars_link()) for client in clients for _ in range(3)))
        finally:
            await asyncio.gather(*(client.aclose() for client in clients))
    assert messages.sizes == [12]


@pytest.mark.asyncio
async def test_a_group_is_capped_by_what_the_wallet_can_carry() -> None:
    ton = FakeTon()
    with use_fake_ton(ton):
        async with new_client(wallet_version="V4R2", max_batch=100) as client, recording() as messages:
            await pay(client, 9)
    assert messages.sizes == [4, 4, 1]


@pytest.mark.asyncio
async def test_a_highload_wallet_batches_without_waiting_for_seqnos() -> None:
    ton = FakeTon()
    with use_fake_ton(ton):
        async with new_client(wallet_version="HighloadV3R1", max_batch=50) as client, recording() as messages:
            await pay(client, 20)
    assert messages.sizes == [20]


@pytest.mark.asyncio
async def test_a_group_expires_with_its_earliest_invoice() -> None:
    ton = FakeTon()
    with use_fake_ton(ton):
        async with new_client(max_batch=4) as client:
            early, late, open_ended = await asyncio.gather(
                process_transaction(client, stars_link(valid_for=30)),
                process_transaction(client, stars_link(valid_for=300)),
                process_transaction(client, stars_link(valid_for=None)),
            )
    assert early.valid_until == late.valid_until == open_ended.valid_until
    assert early.valid_until <= int(time.time()) + 30


@pytest.mark.asyncio
async def test_a_failing_hook_stops_the_whole_group() -> None:
    ton = FakeTon()

    async def refuse(_: TransferIntent) -> None:
        raise RuntimeError("database is down")

    with use_fake_ton(ton):
        async with new_client(max_batch=4) as fine, new_client(max_batch=4, on_transfer_prepared=refuse) as failing:
            results = await asyncio.gather(
                process_transaction(fine, stars_link()), process_transaction(failing, stars_link()), return_exceptions=True
            )
    assert all(isinstance(result, RuntimeError) for result in results)
    assert ton.sent == []


@pytest.mark.asyncio
async def test_every_payment_gets_its_own_hook_call_with_the_shared_hash() -> None:
    ton = FakeTon()
    seen: list[TransferIntent] = []

    async def hook(intent: TransferIntent) -> None:
        seen.append(intent)

    with use_fake_ton(ton):
        async with new_client(max_batch=4, on_transfer_prepared=hook) as client:
            intents = await pay(client, 3)
    assert seen == intents
    assert len({intent.msg_hash for intent in intents}) == 1


@pytest.mark.asyncio
async def test_a_cancelled_payment_does_not_hold_up_the_others() -> None:
    ton = FakeTon()
    with use_fake_ton(ton):
        async with new_client(max_batch=4) as client, recording() as messages:
            tasks = [asyncio.ensure_future(process_transaction(client, stars_link())) for _ in range(3)]
            await asyncio.sleep(0)
            tasks[1].cancel()
            results = await asyncio.gather(*tasks, return_exceptions=True)
    assert isinstance(results[1], asyncio.CancelledError)
    assert isinstance(results[0], TransferIntent) and isinstance(results[2], TransferIntent)
    assert messages.sizes == [2]


# Settling single entries


def entry(deadline: int | None) -> Entry:
    request = TransferRequest(
        builder=None,  # type: ignore[arg-type]
        destination="0:abc",
        amount_nano=STARS_NANO,
        comment=None,
        payment_method=PaymentMethod.GRAM,
        req_id=None,
        deadline=deadline,
        on_prepared=None,
    )
    return Entry(request, wallet=None, done=asyncio.get_event_loop().create_future())  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_expired_entries_fail_as_retryable_and_the_rest_stay() -> None:
    expired, open_ended = entry(int(time.time()) - 1), entry(None)
    assert drop_expired([expired, open_ended]) == [open_ended]
    error = expired.done.exception()
    assert isinstance(error, TransactionError) and error.retryable


# Any kind of purchase queues the same way


async def fragment_answers(method: Any, data: Any = None, *, page_url: str = "") -> dict[str, Any]:
    name = str(method)
    if name.endswith("Recipient"):
        return {"found": {"recipient": "recipient_token"}}
    if name.startswith("init"):
        return {"req_id": f"req_{time.monotonic_ns()}"}
    if name.endswith("Link"):
        return stars_link()
    if name.endswith("State"):
        return {"ok": True, "need_update": False, "mode": "done"}
    return {"ok": True}


@pytest.mark.asyncio
async def test_every_kind_of_purchase_goes_into_the_same_message() -> None:
    ton = FakeTon()
    with use_fake_ton(ton):
        async with new_client(max_batch=10, confirm_timeout=1) as client, recording() as messages:
            with patch.object(client, "call", fragment_answers):
                results = await asyncio.gather(
                    client.purchase_stars("@user", amount=50),
                    client.purchase_stars("@user", amount=50, payment_method=PaymentMethod.USDT_GRAM),
                    client.purchase_premium("@user", months=3),
                    client.topup_gram("@user", amount=1),
                    client.recharge_ads("@channel", amount=1),
                    client.giveaway_stars("@channel", winners=1, amount=500),
                    client.giveaway_premium("@channel", winners=1, months=3),
                )
    assert messages.sizes == [7]
    assert len({result.transaction_id for result in results}) == 1
    assert all(result.confirmed for result in results)
