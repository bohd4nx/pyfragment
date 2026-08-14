"""Cover cancel_invoice, confirm_purchase, and the is_confirmed helper in pyfragment.domains.payments."""

from unittest.mock import AsyncMock, patch

import pytest

from pyfragment import FragmentClient
from pyfragment.domains.payments import cancel_invoice, confirm_purchase, is_confirmed, state_nonce
from tests.shared import FAKE_ACCOUNT, FAKE_REQ_ID, FAKE_TX_BOC

STATE_METHOD = "updateStarsBuyState"
PAGE_URL = "https://fragment.com/stars/buy"

# state_nonce


def test_state_nonce_in_range() -> None:
    for _ in range(20):
        value = int(state_nonce())
        assert 100_000_000 <= value <= 2_147_483_647


# cancel_invoice


@pytest.mark.asyncio
async def test_cancel_invoice_calls_cancel_invoice_method(client: FragmentClient) -> None:
    call_mock = AsyncMock(return_value={"ok": True})
    with patch.object(client, "call", call_mock):
        await cancel_invoice(client, FAKE_REQ_ID, PAGE_URL)

    call_mock.assert_awaited_once_with("cancelInvoice", {"req_id": FAKE_REQ_ID}, page_url=PAGE_URL)


@pytest.mark.asyncio
async def test_cancel_invoice_swallows_errors(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(side_effect=RuntimeError("network down"))):
        await cancel_invoice(client, FAKE_REQ_ID, PAGE_URL)  # must not raise


# is_confirmed


def test_is_confirmed_true_when_need_update_false() -> None:
    assert is_confirmed({"ok": True, "need_update": False, "mode": "done"}) is True


def test_is_confirmed_false_when_need_update_true() -> None:
    assert is_confirmed({"ok": True, "need_update": True, "mode": "processing"}) is False


def test_is_confirmed_false_when_missing_need_update() -> None:
    assert is_confirmed({"ok": True}) is False


def test_is_confirmed_false_when_none() -> None:
    assert is_confirmed(None) is False


# confirm_purchase


@pytest.mark.asyncio
async def test_confirm_purchase_posts_boc_to_confirm_method(client: FragmentClient) -> None:
    transaction_data = {"confirm_method": "confirmReq", "confirm_params": {"id": FAKE_REQ_ID}}
    call_mock = AsyncMock(
        side_effect=[
            {"ok": True},  # confirmReq
            {"ok": True, "need_update": False, "mode": "done"},  # state poll
        ]
    )
    with patch.object(client, "call", call_mock):
        response = await confirm_purchase(client, FAKE_ACCOUNT, FAKE_TX_BOC, transaction_data, STATE_METHOD, PAGE_URL)

    assert response == {"ok": True, "need_update": False, "mode": "done"}
    confirm_call = call_mock.await_args_list[0]
    assert confirm_call.args[0] == "confirmReq"
    assert confirm_call.args[1]["boc"] == FAKE_TX_BOC
    assert confirm_call.args[1]["id"] == FAKE_REQ_ID


@pytest.mark.asyncio
async def test_confirm_purchase_skips_confirm_call_when_no_confirm_method(client: FragmentClient) -> None:
    transaction_data: dict[str, object] = {}
    call_mock = AsyncMock(return_value={"ok": True, "need_update": False, "mode": "done"})
    with patch.object(client, "call", call_mock):
        response = await confirm_purchase(client, FAKE_ACCOUNT, FAKE_TX_BOC, transaction_data, STATE_METHOD, PAGE_URL)

    assert response is not None
    assert response["mode"] == "done"
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
        patch("pyfragment.domains.payments.CONFIRM_STATE_POLL_INTERVAL", 0),
    ):
        response = await confirm_purchase(client, FAKE_ACCOUNT, FAKE_TX_BOC, {}, STATE_METHOD, PAGE_URL)

    assert response is not None
    assert response["mode"] == "done"
    assert call_mock.await_count == 3
    # each poll after the first should carry the mode the previous response reported
    assert call_mock.await_args_list[1].args[1]["mode"] == "new"
    assert call_mock.await_args_list[2].args[1]["mode"] == "processing"


@pytest.mark.asyncio
async def test_confirm_purchase_times_out_and_returns_last_response(client: FragmentClient) -> None:
    call_mock = AsyncMock(return_value={"ok": True, "need_update": True, "mode": "processing"})
    # A short timeout with a longer poll interval guarantees exactly one poll before the deadline passes.
    with (
        patch.object(client, "call", call_mock),
        patch("pyfragment.domains.payments.CONFIRM_STATE_TIMEOUT", 0.02),
        patch("pyfragment.domains.payments.CONFIRM_STATE_POLL_INTERVAL", 0.2),
    ):
        response = await confirm_purchase(client, FAKE_ACCOUNT, FAKE_TX_BOC, {}, STATE_METHOD, PAGE_URL)

    assert response == {"ok": True, "need_update": True, "mode": "processing"}
    assert is_confirmed(response) is False
    call_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_confirm_purchase_swallows_errors(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(side_effect=RuntimeError("network down"))):
        response = await confirm_purchase(client, FAKE_ACCOUNT, FAKE_TX_BOC, {}, STATE_METHOD, PAGE_URL)

    assert response is None
