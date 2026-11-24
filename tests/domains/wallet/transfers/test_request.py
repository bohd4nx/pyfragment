"""process_transaction: turning Fragment's transaction payload into one signed, sent transfer."""

import base64
import time
from collections.abc import Callable
from typing import Any

import pytest

from pyfragment import FragmentClient, TransactionError, TransferIntent
from pyfragment.domains.wallet.transfers import process_transaction
from pyfragment.enums import PaymentMethod
from tests.domains.wallet.helpers import asked, link
from tests.support.fake_ton import FakeTon


class TestProcessTransaction:
    async def test_sends_the_transfer_once_and_describes_it(self, fake_ton: FakeTon, client: FragmentClient) -> None:
        message = asked()

        sent = await process_transaction(client, link(), PaymentMethod.USDT_GRAM, req_id="req_42")

        assert len(fake_ton.sent) == 1 and fake_ton.landed == fake_ton.sent
        assert isinstance(sent, TransferIntent)
        assert sent.amount_nano == int(message["amount"])
        assert sent.destination == message["address"]
        assert sent.comment == "50 Telegram Stars \n\nRef#nd7jvgt6H"
        assert (sent.req_id, sent.payment_method) == ("req_42", PaymentMethod.USDT_GRAM)
        assert len(sent.msg_hash) == 64

    async def test_returned_boc_is_what_was_broadcast(self, fake_ton: FakeTon, client: FragmentClient) -> None:
        sent = await process_transaction(client, link())
        assert base64.b64decode(sent.boc) == fake_ton.sent[0]

    @pytest.mark.parametrize(
        "data",
        [
            {"transaction": {}},
            {"transaction": {"messages": []}},
            link(amount="0.5"),
            link(amount="-1"),
            link(amount=True),
            link(address=""),
            link(address="not-an-address"),
            link(address=5),
        ],
        ids=[
            "no-messages",
            "empty-messages",
            "fractional-amount",
            "negative-amount",
            "bool-amount",
            "empty-address",
            "bad-address",
            "int-address",
        ],
    )
    async def test_invalid_payload_raises_before_signing(
        self, fake_ton: FakeTon, client: FragmentClient, data: dict[str, Any]
    ) -> None:
        with pytest.raises(TransactionError, match="invalid transaction payload"):
            await process_transaction(client, data)
        assert fake_ton.sent == [] and fake_ton.seqno_reads == 0

    async def test_multi_message_transaction_is_refused(self, fake_ton: FakeTon, client: FragmentClient) -> None:
        # Signing only the first message would pay part of the invoice.
        data = link()
        data["transaction"]["messages"] *= 2
        with pytest.raises(TransactionError, match="2 messages"):
            await process_transaction(client, data)
        assert fake_ton.sent == []

    async def test_expired_transaction_is_not_signed(self, fake_ton: FakeTon, client: FragmentClient) -> None:
        with pytest.raises(TransactionError, match="expired") as exc_info:
            await process_transaction(client, link(valid_for=-1))
        assert exc_info.value.retryable
        assert fake_ton.sent == [] and fake_ton.seqno_reads == 0

    async def test_transaction_without_a_deadline_is_signed(self, fake_ton: FakeTon, client: FragmentClient) -> None:
        sent = await process_transaction(client, link(valid_for=None))
        assert sent.valid_until <= int(time.time()) + 60
        assert len(fake_ton.sent) == 1

    async def test_hook_gets_the_intent_before_the_send(
        self, fake_ton: FakeTon, make_client: Callable[..., FragmentClient]
    ) -> None:
        seen: list[tuple[TransferIntent, int]] = []

        async def hook(intent: TransferIntent) -> None:
            seen.append((intent, len(fake_ton.sent)))

        sent = await process_transaction(make_client(on_transfer_prepared=hook), link())

        assert seen == [(sent, 0)]

    async def test_failing_hook_stops_the_transfer(self, fake_ton: FakeTon, make_client: Callable[..., FragmentClient]) -> None:
        async def hook(intent: TransferIntent) -> None:
            raise RuntimeError("database is down")

        with pytest.raises(RuntimeError, match="database is down"):
            await process_transaction(make_client(on_transfer_prepared=hook), link())
        assert fake_ton.sent == []
