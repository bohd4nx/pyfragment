"""Look the wallet's transfers up on-chain with find_transfer(), on a real mainnet transaction."""

import copy
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from ton_core import Slice, Transaction

from pyfragment import ConfigurationError, FragmentClient, ProviderError, TransferInfo
from pyfragment.domains.wallet.transfer import _find_transfer_by_lt  # white-box: testing lt-bound logic directly
from tests.fake_ton import FakeTon, provider_error, use_fake_ton
from tests.shared import fixture_json

PAYMENT = fixture_json("wallet_payment_transaction.json")
PAID_AT = datetime.fromtimestamp(PAYMENT["utime"], UTC)


def payment() -> Any:
    tx = Transaction.deserialize(Slice.one_from_boc(PAYMENT["raw"]))
    assert isinstance(tx, Transaction)
    return tx


def filler(lt: int, utime: int) -> SimpleNamespace:
    """An unrelated transaction: nothing to match in it."""
    return SimpleNamespace(lt=lt, now=utime, in_msg=None, out_msgs=[])


def ton_with(*transactions: Any) -> FakeTon:
    ton = FakeTon()
    ton.transactions = list(transactions)
    return ton


@pytest.mark.asyncio
async def test_finds_a_transfer_by_message_hash(client: FragmentClient) -> None:
    with use_fake_ton(ton_with(filler(PAYMENT["lt"] + 5, PAYMENT["utime"] + 9), payment())):
        found = await client.find_transfer(msg_hash=PAYMENT["in_msg_hash"], since=PAID_AT - timedelta(minutes=1))

    assert found == TransferInfo(
        hash=PAYMENT["hash"],
        lt=PAYMENT["lt"],
        utime=PAYMENT["utime"],
        msg_hash=PAYMENT["in_msg_hash"],
        comment=PAYMENT["comment"],
        success=True,
    )


@pytest.mark.asyncio
async def test_finds_a_transfer_by_comment(client: FragmentClient) -> None:
    with use_fake_ton(ton_with(payment())):
        found = await client.find_transfer(comment=PAYMENT["comment"], since=PAID_AT)
    assert found is not None and found.hash == PAYMENT["hash"]


@pytest.mark.asyncio
async def test_message_hash_is_matched_case_insensitively(client: FragmentClient) -> None:
    with use_fake_ton(ton_with(payment())):
        assert await client.find_transfer(msg_hash=PAYMENT["in_msg_hash"].upper(), since=PAID_AT) is not None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query",
    [
        {"msg_hash": "00" * 32},
        {"comment": "50 Telegram Stars \n\nRef#other"},
        {"msg_hash": PAYMENT["in_msg_hash"], "comment": "x"},
    ],
    ids=["other-hash", "other-comment", "both-must-match"],
)
async def test_other_transfers_are_not_found(client: FragmentClient, query: dict[str, str]) -> None:
    with use_fake_ton(ton_with(payment())):
        assert await client.find_transfer(since=PAID_AT, **query) is None


@pytest.mark.asyncio
async def test_search_stops_at_since(client: FragmentClient) -> None:
    ton = ton_with(payment())
    with use_fake_ton(ton):
        found = await client.find_transfer(msg_hash=PAYMENT["in_msg_hash"], since=PAID_AT + timedelta(seconds=1))
    assert found is None


@pytest.mark.asyncio
async def test_search_pages_through_history(client: FragmentClient) -> None:
    newer = [filler(PAYMENT["lt"] + i, PAYMENT["utime"] + i) for i in range(5, 0, -1)]
    ton = ton_with(*newer, payment())
    calls = AsyncMock(wraps=ton.get_transactions)
    ton.get_transactions = calls  # type: ignore[method-assign]
    with use_fake_ton(ton), patch("pyfragment.domains.wallet.transfer.TRANSACTIONS_PAGE_SIZE", 2):
        found = await client.find_transfer(msg_hash=PAYMENT["in_msg_hash"], since=PAID_AT)
    assert found is not None
    assert [c.kwargs["from_lt"] for c in calls.await_args_list] == [None, PAYMENT["lt"] + 3, PAYMENT["lt"] + 1]


@pytest.mark.asyncio
async def test_query_is_required(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError, match="msg_hash or comment"):
        await client.find_transfer(since=PAID_AT)


@pytest.mark.asyncio
async def test_unreadable_history_raises_instead_of_reporting_not_found(client: FragmentClient) -> None:
    ton = ton_with(payment())
    ton.transaction_errors = [provider_error(401, "unauthorized")]
    with use_fake_ton(ton):
        with pytest.raises(ProviderError, match="unauthorized") as exc_info:
            await client.find_transfer(msg_hash=PAYMENT["in_msg_hash"], since=PAID_AT)
    assert exc_info.value.status == 401


def _with(change: str) -> Any:
    tx = payment()
    description = copy.copy(tx.description)
    if change == "aborted":
        description.aborted = True
    elif change == "skipped":
        # A transfer the wallet couldn't afford is skipped silently while the transaction succeeds.
        description.action = copy.copy(description.action)
        description.action.skipped_actions = 1
    elif change == "compute-failed":
        description.compute_ph = copy.copy(description.compute_ph)
        description.compute_ph.success = False
    tx.description = description
    return tx


@pytest.mark.asyncio
@pytest.mark.parametrize("change", ["aborted", "skipped", "compute-failed"])
async def test_failed_transfers_are_found_but_not_successful(client: FragmentClient, change: str) -> None:
    with use_fake_ton(ton_with(_with(change))):
        found = await client.find_transfer(msg_hash=PAYMENT["in_msg_hash"], since=PAID_AT)
    assert found is not None and found.success is False


# _find_transfer_by_lt: lt lower bound prevents returning pre-existing transactions


@pytest.mark.asyncio
async def test_lt_lower_bound_skips_transactions_at_or_before_last_lt(client: FragmentClient) -> None:
    ton = ton_with(filler(PAYMENT["lt"] + 1, PAYMENT["utime"]), payment())
    with use_fake_ton(ton):
        found = await _find_transfer_by_lt(client, msg_hash=PAYMENT["in_msg_hash"], last_lt=PAYMENT["lt"])
    assert found is None


@pytest.mark.asyncio
async def test_lt_lower_bound_finds_transfer_above_threshold(client: FragmentClient) -> None:
    ton = ton_with(payment())
    with use_fake_ton(ton):
        found = await _find_transfer_by_lt(client, msg_hash=PAYMENT["in_msg_hash"], last_lt=PAYMENT["lt"] - 1)
    assert found is not None and found.hash == PAYMENT["hash"]
