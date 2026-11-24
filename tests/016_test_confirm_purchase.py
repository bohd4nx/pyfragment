"""Cover state_nonce and confirm_purchase from pyfragment.domains.payments."""

from unittest.mock import AsyncMock, patch

import pytest

from pyfragment import FragmentClient
from pyfragment.domains.payments import confirm_purchase, state_nonce
from pyfragment.domains.purchases.stars import STARS_FLOW
from tests.shared import FAKE_ACCOUNT, FAKE_CONFIRM_METHOD, FAKE_REQ_ID, FAKE_TX_BOC

STATE_METHOD = STARS_FLOW.state_method

# state_nonce


def test_state_nonce_in_range() -> None:
    for _ in range(20):
        value = int(state_nonce())
        assert 100_000_000 <= value <= 2_147_483_647


# confirm_purchase


@pytest.mark.asyncio
async def test_confirm_purchase_posts_boc_to_confirm_method(client: FragmentClient) -> None:
    transaction_data = {"confirm_method": FAKE_CONFIRM_METHOD, "confirm_params": {"id": FAKE_REQ_ID}}
    call_mock = AsyncMock(
        side_effect=[
            {"ok": True},  # confirmReq
            {"ok": True, "need_update": False, "mode": "done"},  # state poll
        ]
    )
    with patch.object(client, "call", call_mock):
        confirmed = await confirm_purchase(client, STARS_FLOW, FAKE_ACCOUNT, FAKE_TX_BOC, transaction_data)

    assert confirmed is True
    confirm_call = call_mock.await_args_list[0]
    assert confirm_call.args[0] == FAKE_CONFIRM_METHOD
    assert confirm_call.args[1]["boc"] == FAKE_TX_BOC
    assert confirm_call.args[1]["id"] == FAKE_REQ_ID


@pytest.mark.asyncio
async def test_confirm_purchase_skips_confirm_call_when_no_confirm_method(client: FragmentClient) -> None:
    transaction_data: dict[str, object] = {}
    call_mock = AsyncMock(return_value={"ok": True, "need_update": False, "mode": "done"})
    with patch.object(client, "call", call_mock):
        confirmed = await confirm_purchase(client, STARS_FLOW, FAKE_ACCOUNT, FAKE_TX_BOC, transaction_data)

    assert confirmed is True
    call_mock.assert_awaited_once()
    assert call_mock.await_args.args[0] == STATE_METHOD
    # Fragment's own frontend always polls this endpoint with lv=false, never lv=1.
    assert call_mock.await_args.args[1]["lv"] == "false"


@pytest.mark.asyncio
async def test_confirm_purchase_polls_until_done(client: FragmentClient) -> None:
    call_mock = AsyncMock(
        side_effect=[
            {"ok": True, "need_update": True, "mode": "new"},
            {"ok": True, "need_update": True, "mode": "processing"},
            {"ok": True, "need_update": False, "mode": "done"},
        ]
    )
    with (
        patch.object(client, "call", call_mock),
        patch("pyfragment.domains.payments.confirmation.CONFIRM_STATE_POLL_INTERVAL", 0),
    ):
        confirmed = await confirm_purchase(client, STARS_FLOW, FAKE_ACCOUNT, FAKE_TX_BOC, {})

    assert confirmed is True
    assert call_mock.await_count == 3
    # each poll after the first should carry the mode the previous response reported
    assert call_mock.await_args_list[1].args[1]["mode"] == "new"
    assert call_mock.await_args_list[2].args[1]["mode"] == "processing"


@pytest.mark.asyncio
async def test_confirm_purchase_times_out_and_returns_last_response(client: FragmentClient) -> None:
    call_mock = AsyncMock(return_value={"ok": True, "need_update": True, "mode": "processing"})
    # A short timeout with a longer poll interval guarantees exactly one poll before the deadline passes.
    client.confirm_timeout = 0.02
    with (
        patch.object(client, "call", call_mock),
        patch("pyfragment.domains.payments.confirmation.CONFIRM_STATE_POLL_INTERVAL", 0.2),
    ):
        confirmed = await confirm_purchase(client, STARS_FLOW, FAKE_ACCOUNT, FAKE_TX_BOC, {})

    assert confirmed is False
    call_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_confirm_purchase_swallows_errors(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(side_effect=RuntimeError("network down"))):
        confirmed = await confirm_purchase(client, STARS_FLOW, FAKE_ACCOUNT, FAKE_TX_BOC, {})

    assert confirmed is False


@pytest.mark.asyncio
async def test_zero_confirm_timeout_reports_the_purchase_without_polling(client: FragmentClient) -> None:
    client.confirm_timeout = 0
    transaction_data = {"confirm_method": FAKE_CONFIRM_METHOD, "confirm_params": {"id": FAKE_REQ_ID}}
    call_mock = AsyncMock(return_value={"ok": True})
    with patch.object(client, "call", call_mock):
        confirmed = await confirm_purchase(client, STARS_FLOW, FAKE_ACCOUNT, FAKE_TX_BOC, transaction_data)

    # Fragment is still told about the transfer, but nobody waits for it.
    call_mock.assert_awaited_once()
    assert call_mock.await_args.args[0] == FAKE_CONFIRM_METHOD
    assert confirmed is False
