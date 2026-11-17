"""Sign and send Fragment transactions with a real wallet against an in-memory provider: the seqno and
expiry that get signed, and how the library handles send errors."""

import asyncio
import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import pytest
from ton_core import ContractState

from pyfragment import (
    FragmentClient,
    ProviderError,
    TransactionError,
    TransferIntent,
)
from pyfragment.domains.wallet.transfers import process_transaction
from pyfragment.enums import PaymentMethod
from tests.fake_ton import FakeTon, provider_error, use_fake_ton
from tests.shared import VALID_API_KEY, VALID_COOKIES, VALID_SEED
from tests.signing import external_message_body, has_state_init, split_leading_signature, split_signature, w5_header

FRAGMENT_ADDRESS = "UQCFJEP4WZ_mpdo0_kMEmsTgvrMHG7K_tWY16pQhKHwoOtFz"
STARS_PAYLOAD = "te6ccgEBAQEAJwAASgAAAAA1MCBUZWxlZ3JhbSBTdGFycyAKClJlZiNrcEo1NWgzQlc="


def transaction(amount: str = "500000000", valid_until: int | None = None, messages: int = 1) -> dict[str, Any]:
    """A Fragment transaction paying 0.5 GRAM (ex TON) by default, valid for 5 more minutes."""
    message = {"address": FRAGMENT_ADDRESS, "amount": amount, "payload": STARS_PAYLOAD}
    return {
        "transaction": {
            "validUntil": valid_until if valid_until is not None else int(time.time()) + 300,
            "from": "0:" + "0" * 64,
            "messages": [message] * messages,
        }
    }


@asynccontextmanager
async def fragment_client(ton: FakeTon, **options: Any) -> AsyncIterator[FragmentClient]:
    with use_fake_ton(ton):
        async with FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES, **options) as client:
            yield client


def signed_header(boc: bytes) -> tuple[int, int]:
    """``(valid_until, seqno)`` the wallet signed into a sent message."""
    _, body = external_message_body(boc)
    return w5_header(split_signature(body)[0])


# Sending a valid transaction


@pytest.mark.asyncio
async def test_sufficient_balance_sends_once() -> None:
    ton = FakeTon(balance=1_000_000_000)
    async with fragment_client(ton) as client:
        sent = await process_transaction(client, transaction())

    assert isinstance(sent, TransferIntent)
    assert len(ton.sent) == 1 and ton.landed == ton.sent
    assert sent.amount_nano == 500_000_000
    assert sent.destination == FRAGMENT_ADDRESS
    assert sent.comment == "50 Telegram Stars \n\nRef#kpJ55h3BW"
    assert len(sent.msg_hash) == 64


# Fragment's payload


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "data",
    [{"transaction": {}}, {"transaction": {"messages": []}}, transaction(amount="0.5"), transaction(amount="-1")],
    ids=["no-messages", "empty-messages", "fractional-amount", "negative-amount"],
)
async def test_invalid_payload_raises_before_signing(data: dict[str, Any]) -> None:
    ton = FakeTon()
    async with fragment_client(ton) as client:
        with pytest.raises(TransactionError, match="invalid transaction payload"):
            await process_transaction(client, data)
    assert ton.sent == []


@pytest.mark.asyncio
async def test_multi_message_transaction_is_refused() -> None:
    # Signing only the first message would pay part of the invoice.
    ton = FakeTon()
    async with fragment_client(ton) as client:
        with pytest.raises(TransactionError, match="2 messages"):
            await process_transaction(client, transaction(messages=2))
    assert ton.sent == []


@pytest.mark.asyncio
async def test_expired_transaction_is_not_signed() -> None:
    ton = FakeTon()
    async with fragment_client(ton) as client:
        with pytest.raises(TransactionError, match="expired") as exc_info:
            await process_transaction(client, transaction(valid_until=int(time.time()) - 1))
    assert exc_info.value.retryable
    assert ton.sent == [] and ton.seqno_reads == 0


# What gets signed


@pytest.mark.asyncio
async def test_signs_the_on_chain_seqno() -> None:
    ton = FakeTon(seqno=41)
    async with fragment_client(ton) as client:
        await process_transaction(client, transaction())
    assert signed_header(ton.sent[0])[1] == 41


@pytest.mark.asyncio
async def test_seqno_read_failure_raises_instead_of_signing_seqno_zero() -> None:
    ton = FakeTon(seqno=41)
    ton.seqno_errors = [provider_error(500, "internal")]
    async with fragment_client(ton) as client:
        with pytest.raises(ProviderError) as exc_info:
            await process_transaction(client, transaction())
    assert exc_info.value.retryable
    assert ton.sent == []


@pytest.mark.asyncio
async def test_undeployed_wallet_signs_seqno_zero_and_ships_its_state_init() -> None:
    ton = FakeTon(state=ContractState.UNINIT, seqno=0)
    async with fragment_client(ton) as client:
        await process_transaction(client, transaction())
    assert signed_header(ton.sent[0])[1] == 0
    assert has_state_init(ton.sent[0])


@pytest.mark.asyncio
async def test_deployed_wallet_does_not_ship_its_state_init() -> None:
    ton = FakeTon(state=ContractState.ACTIVE)
    async with fragment_client(ton) as client:
        await process_transaction(client, transaction())
    assert not has_state_init(ton.sent[0])


@pytest.mark.asyncio
async def test_transfer_expires_with_fragment_deadline_when_that_is_sooner() -> None:
    ton = FakeTon()
    deadline = int(time.time()) + 20
    async with fragment_client(ton) as client:
        sent = await process_transaction(client, transaction(valid_until=deadline))
    assert signed_header(ton.sent[0])[0] == deadline == sent.valid_until


@pytest.mark.asyncio
async def test_transfer_expires_within_a_minute_otherwise() -> None:
    ton = FakeTon()
    before = int(time.time())
    async with fragment_client(ton) as client:
        await process_transaction(client, transaction(valid_until=before + 3600))
    assert before + 60 <= signed_header(ton.sent[0])[0] <= int(time.time()) + 60


# Sending


@pytest.mark.asyncio
async def test_send_error_on_a_transfer_that_landed_is_a_success() -> None:
    # toncenter answers 500 to some sends that went through: the error is logged and the result returned normally.
    ton = FakeTon(seqno=5)
    ton.send_errors = [(provider_error(500, "internal"), True)]
    async with fragment_client(ton) as client:
        sent = await process_transaction(client, transaction())
    assert len(ton.sent) == 1 and len(ton.landed) == 1 and ton.seqno == 6
    assert sent.comment == "50 Telegram Stars \n\nRef#kpJ55h3BW"


@pytest.mark.asyncio
async def test_definite_send_rejection_raises_non_retryable_provider_error() -> None:
    # A 4xx response from the provider means the message was definitively rejected — not sent.
    ton = FakeTon()
    ton.send_errors = [(provider_error(401, "invalid token"), False)]
    async with fragment_client(ton) as client:
        with pytest.raises(ProviderError, match="401") as exc_info:
            await process_transaction(client, transaction())
    assert not exc_info.value.retryable
    assert ton.landed == []  # provider rejected — nothing actually landed on-chain


@pytest.mark.asyncio
async def test_ambiguous_send_error_is_logged_and_result_returned(caplog: pytest.LogCaptureFixture) -> None:
    # A non-4xx error (e.g. RuntimeError, network drop) is ambiguous — the message may have gone through.
    ton = FakeTon()
    ton.send_errors = [(RuntimeError("connection reset"), False)]
    async with fragment_client(ton) as client:
        with caplog.at_level(logging.WARNING, logger="pyfragment"):
            sent = await process_transaction(client, transaction())
    assert "Failed to send transfer" in caplog.text
    assert isinstance(sent, TransferIntent)


# The on_transfer_prepared hook


@pytest.mark.asyncio
async def test_hook_gets_the_signed_transfer_before_it_is_sent() -> None:
    ton = FakeTon()
    seen: list[tuple[TransferIntent, int]] = []

    async def hook(intent: TransferIntent) -> None:
        seen.append((intent, len(ton.sent)))

    async with fragment_client(ton, on_transfer_prepared=hook) as client:
        sent = await process_transaction(client, transaction(), req_id="req_42")

    assert seen == [(sent, 0)]
    assert sent.req_id == "req_42" and sent.payment_method == PaymentMethod.GRAM


@pytest.mark.asyncio
async def test_failing_hook_stops_the_transfer() -> None:
    ton = FakeTon()

    async def hook(intent: TransferIntent) -> None:
        raise RuntimeError("database is down")

    async with fragment_client(ton, on_transfer_prepared=hook) as client:
        with pytest.raises(RuntimeError, match="database is down"):
            await process_transaction(client, transaction())
    assert ton.sent == []


# One transfer at a time


@pytest.mark.asyncio
async def test_concurrent_purchases_from_one_client_use_consecutive_seqnos() -> None:
    ton = FakeTon(seqno=5)
    async with fragment_client(ton) as client:
        await asyncio.gather(process_transaction(client, transaction()), process_transaction(client, transaction()))
    assert sorted(signed_header(boc)[1] for boc in ton.sent) == [5, 6]
    assert len(ton.landed) == 2


@pytest.mark.asyncio
async def test_second_transfer_takes_its_seqno_from_the_chain_once_the_first_landed() -> None:
    # A node rejects a seqno that is ahead of the chain, so the next transfer never counts on from the pending one.
    ton = FakeTon(seqno=5)
    async with fragment_client(ton) as client:
        await process_transaction(client, transaction())
        reads_after_first = ton.seqno_reads
        await process_transaction(client, transaction())
    assert sorted(signed_header(boc)[1] for boc in ton.sent) == [5, 6]
    assert ton.seqno_reads == reads_after_first + 1


# Wallets without a seqno


def highload_expiry(boc: bytes, wallet_version: str) -> int:
    """When a signed highload message stops being accepted."""
    _, body = external_message_body(boc)
    if wallet_version == "HighloadV2":
        signed, _ = split_leading_signature(body)
        reader = signed.begin_parse()
        reader.skip_bits(32)  # subwallet id
        return int(reader.load_uint(64) >> 32)  # bounded query id: expiry << 32 | query id
    signed, _ = split_leading_signature(body, signed_in_ref=True)
    reader = signed.begin_parse()
    reader.skip_bits(32 + 8 + 23)  # subwallet id, (message ref), send mode, query id
    created_at = reader.load_uint(64)
    return int(created_at + reader.load_uint(22))  # created_at + timeout


@pytest.mark.asyncio
@pytest.mark.parametrize("wallet_version", ["HighloadV2", "HighloadV3R1"])
@pytest.mark.parametrize("seconds_left", [20, 3600])
async def test_highload_transfers_expire_like_the_others(wallet_version: str, seconds_left: int) -> None:
    # No seqno here: the expiry is what keeps a highload transfer from paying an invoice Fragment already dropped.
    ton = FakeTon()
    async with fragment_client(ton, wallet_version=wallet_version) as client:
        sent = await process_transaction(client, transaction(valid_until=int(time.time()) + seconds_left))
    assert len(ton.sent) == 1 and ton.seqno_reads == 0
    expiry = highload_expiry(ton.sent[0], wallet_version)
    assert expiry == sent.valid_until
    assert expiry <= int(time.time()) + min(seconds_left, 60)
