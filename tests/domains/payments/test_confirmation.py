"""Reporting the broadcast transaction to Fragment and waiting for it to be processed."""

import pytest

from pyfragment import FragmentClient
from pyfragment.domains.payments import confirm_purchase
from pyfragment.domains.payments.confirmation import wait_for_confirmation
from pyfragment.domains.payments.flow import PurchaseFlow
from pyfragment.enums import ApiMethod, StateMode
from tests.support.data import ACCOUNT, REQ_ID, TX_BOC
from tests.support.fake_fragment import FakeFragment

FLOW = PurchaseFlow(
    search_method=ApiMethod.SEARCH_STARS_RECIPIENT,
    page_url="https://fragment.com/stars/buy",
    state_method=ApiMethod.UPDATE_STARS_BUY_STATE,
    init_method=ApiMethod.INIT_BUY_STARS_REQUEST,
    link_method=ApiMethod.GET_BUY_STARS_LINK,
    label="Test purchase",
)
CONFIRM_METHOD = "confirmReq"  # named by Fragment in the transaction payload, not a fixed API method
TRANSACTION = {"confirm_method": CONFIRM_METHOD, "confirm_params": {"id": REQ_ID}}
DONE = {"ok": True, "need_update": False, "mode": StateMode.DONE}


def pending(mode: StateMode) -> dict[str, object]:
    return {"ok": True, "need_update": True, "mode": mode}


@pytest.fixture(autouse=True)
def no_polling_delay(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("pyfragment.domains.payments.confirmation.CONFIRM_STATE_POLL_INTERVAL", 0)


class TestConfirmPurchase:
    async def test_posts_the_boc_to_the_confirm_method_then_polls(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(CONFIRM_METHOD, {"ok": True}).reply(FLOW.state_method, DONE)

        assert await confirm_purchase(client, FLOW, ACCOUNT, TX_BOC, TRANSACTION) is True

        assert fragment.methods == [CONFIRM_METHOD, FLOW.state_method]
        confirm = fragment.calls[0]
        assert confirm.data["boc"] == TX_BOC
        assert confirm.data["id"] == REQ_ID
        assert "account" in confirm.data and "device" in confirm.data
        assert confirm.page_url == FLOW.page_url

    async def test_without_a_confirm_method_it_only_polls(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(FLOW.state_method, DONE)

        assert await confirm_purchase(client, FLOW, ACCOUNT, TX_BOC, {}) is True

        assert fragment.methods == [FLOW.state_method]
        assert fragment.calls[0].data["lv"] == "false"  # Fragment's frontend never polls with lv=1

    async def test_polls_until_fragment_is_done_passing_each_reported_mode_back(
        self, client: FragmentClient, fragment: FakeFragment
    ) -> None:
        fragment.reply(FLOW.state_method, pending(StateMode.NEW), pending(StateMode.PROCESSING), DONE)

        assert await confirm_purchase(client, FLOW, ACCOUNT, TX_BOC, {}) is True

        assert [call.data["mode"] for call in fragment.calls] == [StateMode.NEW, StateMode.NEW, StateMode.PROCESSING]

    async def test_times_out_unconfirmed(self, client: FragmentClient, fragment: FakeFragment) -> None:
        client.confirm_timeout = 0.02
        fragment.reply(FLOW.state_method, pending(StateMode.PROCESSING))

        assert await confirm_purchase(client, FLOW, ACCOUNT, TX_BOC, {}) is False
        assert fragment.calls

    async def test_a_zero_timeout_reports_the_transfer_without_polling(
        self, client: FragmentClient, fragment: FakeFragment
    ) -> None:
        client.confirm_timeout = 0
        fragment.reply(CONFIRM_METHOD, {"ok": True})

        assert await confirm_purchase(client, FLOW, ACCOUNT, TX_BOC, TRANSACTION) is False
        assert fragment.methods == [CONFIRM_METHOD]

    async def test_a_failing_call_leaves_the_purchase_unconfirmed_instead_of_raising(
        self, client: FragmentClient, fragment: FakeFragment
    ) -> None:
        fragment.reply(CONFIRM_METHOD, RuntimeError("network down"))

        assert await confirm_purchase(client, FLOW, ACCOUNT, TX_BOC, TRANSACTION) is False


class TestWaitForConfirmation:
    async def test_state_params_carry_the_nonce_given(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(FLOW.state_method, DONE)

        assert await wait_for_confirmation(client, FLOW, "12345") is True
        assert fragment.calls[0].data == {"mode": StateMode.NEW, "lv": "false", "dh": "12345"}

    async def test_a_response_without_a_mode_keeps_the_current_one(
        self, client: FragmentClient, fragment: FakeFragment
    ) -> None:
        fragment.reply(
            FLOW.state_method,
            {"need_update": True},
            {"need_update": True, "mode": StateMode.PROCESSING},
            {"need_update": True},
            DONE,
        )

        await wait_for_confirmation(client, FLOW, "1")

        assert [call.data["mode"] for call in fragment.calls] == [
            StateMode.NEW,
            StateMode.NEW,
            StateMode.PROCESSING,
            StateMode.PROCESSING,
        ]
