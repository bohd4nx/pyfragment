"""The invoice-based purchase flow end to end: invoice, signing, confirmation; and the page state it polls."""

import re

import pytest

from pyfragment import FragmentAPIError, FragmentClient, InvoiceExpiredError, VerificationError
from pyfragment.domains.payments import PaymentResult, run_purchase, state_nonce
from pyfragment.domains.payments.flow import PurchaseFlow
from pyfragment.enums import ApiError, ApiMethod, PaymentMethod, StateMode
from pyfragment.schemas import PageState
from tests.support import fixtures
from tests.support.data import COMMENT, REQ_ID, SENT, TX_BOC, TX_HASH
from tests.support.fake_fragment import FakeFragment

FLOW = PurchaseFlow(
    search_method=ApiMethod.SEARCH_STARS_RECIPIENT,
    page_url="https://fragment.com/stars/buy",
    state_method=ApiMethod.UPDATE_STARS_BUY_STATE,
    init_method=ApiMethod.INIT_BUY_STARS_REQUEST,
    link_method=ApiMethod.GET_BUY_STARS_LINK,
    label="Test purchase",
)
DONE = {"ok": True, "need_update": False, "mode": StateMode.DONE}


class Signer:
    """Stands in for process_transaction: remembers what it was asked to sign."""

    def __init__(self) -> None:
        self.calls: list[tuple[dict[str, object], PaymentMethod, str]] = []

    async def __call__(
        self, _client: FragmentClient, transaction: dict[str, object], *, payment_method: PaymentMethod, req_id: str
    ):
        self.calls.append((transaction, payment_method, req_id))
        return SENT


@pytest.fixture
def signer(monkeypatch: pytest.MonkeyPatch) -> Signer:
    signer = Signer()
    monkeypatch.setattr("pyfragment.domains.payments.flow.process_transaction", signer)
    monkeypatch.setattr("pyfragment.domains.payments.confirmation.CONFIRM_STATE_POLL_INTERVAL", 0)
    return signer


def script_purchase(fragment: FakeFragment) -> None:
    fragment.reply(FLOW.init_method, fixtures.response("stars_invoice.json"))
    fragment.reply(FLOW.link_method, fixtures.response("stars_transaction_link.json"))
    fragment.reply("confirmReq", {"ok": True})
    fragment.reply(FLOW.state_method, DONE)


class TestRunPurchase:
    async def test_pays_the_invoice_and_reports_the_transfer(
        self, client: FragmentClient, fragment: FakeFragment, signer: Signer
    ) -> None:
        script_purchase(fragment)

        result = await run_purchase(client, FLOW, {"recipient": "r"}, {"show_sender": 0}, PaymentMethod.USDT_GRAM)

        assert result == PaymentResult(transaction_id=TX_HASH, confirmed=True, comment=COMMENT, boc=TX_BOC)
        assert fragment.methods == [FLOW.init_method, FLOW.link_method, "confirmReq", FLOW.state_method]
        assert fragment.calls[0].data == {"recipient": "r"}
        assert fragment.calls[1].data == {"transaction": 1, "id": REQ_ID, "show_sender": 0}
        transaction, payment_method, req_id = signer.calls[0]
        assert transaction == fixtures.response("stars_transaction_link.json")
        assert (payment_method, req_id) == (PaymentMethod.USDT_GRAM, REQ_ID)

    async def test_pays_in_gram_by_default(self, client: FragmentClient, fragment: FakeFragment, signer: Signer) -> None:
        script_purchase(fragment)

        await run_purchase(client, FLOW, {})

        assert signer.calls[0][1] is PaymentMethod.GRAM

    async def test_the_confirmation_names_the_wallet_that_paid(
        self, client: FragmentClient, fragment: FakeFragment, signer: Signer
    ) -> None:
        script_purchase(fragment)

        await run_purchase(client, FLOW, {})

        confirm = fragment.sent("confirmReq")[0].data
        assert confirm["boc"] == TX_BOC and confirm["id"] == REQ_ID
        assert f'"{client.ton_wallet.account_info()["publicKey"]}"' in confirm["account"]

    async def test_unconfirmed_purchase_is_still_reported(
        self, client: FragmentClient, fragment: FakeFragment, signer: Signer
    ) -> None:
        client.confirm_timeout = 0
        script_purchase(fragment)

        result = await run_purchase(client, FLOW, {})

        assert result.confirmed is False and result.transaction_id == TX_HASH

    @pytest.mark.parametrize(
        ("answer", "error"),
        [
            ({"need_verify": True}, VerificationError),
            ({"error": ApiError.INVOICE_EXPIRED}, InvoiceExpiredError),
            ({"error": "Something new"}, FragmentAPIError),
        ],
    )
    async def test_nothing_is_signed_when_fragment_refuses_the_link(
        self, client: FragmentClient, fragment: FakeFragment, signer: Signer, answer: dict[str, object], error: type[Exception]
    ) -> None:
        fragment.reply(FLOW.init_method, fixtures.response("stars_invoice.json")).reply(FLOW.link_method, answer)

        with pytest.raises(error):
            await run_purchase(client, FLOW, {})

        assert signer.calls == []


class TestPurchaseFlow:
    def test_state_params_default_to_a_new_page_with_a_nonce(self) -> None:
        params = FLOW.state_params()

        assert params["mode"] == StateMode.NEW and params["lv"] == "false"
        assert re.fullmatch(r"\d+", params["dh"])

    def test_state_params_take_mode_nonce_and_extras(self) -> None:
        assert FLOW.state_params(StateMode.PROCESSING, "42", stars=500) == {
            "mode": StateMode.PROCESSING,
            "lv": "false",
            "dh": "42",
            "stars": 500,
        }

    async def test_open_makes_the_state_call_of_the_page(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(FLOW.state_method, {"ok": True})

        await FLOW.open(client, stars=500)

        call = fragment.calls[0]
        assert (call.method, call.page_url) == (FLOW.state_method, FLOW.page_url)
        assert call.data["stars"] == 500 and call.data["mode"] == StateMode.NEW


class TestPageState:
    @pytest.mark.parametrize(
        ("response", "mode", "done"),
        [
            ({"need_update": False, "mode": "done"}, "done", True),
            ({"need_update": True, "mode": "processing"}, "processing", False),
            ({"mode": "new"}, "new", False),
            ({"need_update": 0}, StateMode.NEW, True),
        ],
    )
    def test_reads_mode_and_done_flag(self, response: dict[str, object], mode: str, done: bool) -> None:
        state = PageState.from_response(response)
        assert (state.mode, state.is_done) == (mode, done)

    def test_a_missing_mode_falls_back_to_the_given_default(self) -> None:
        assert PageState.from_response({}, default_mode=StateMode.PROCESSING).mode == StateMode.PROCESSING


class TestStateNonce:
    def test_is_a_digit_string_in_the_range_fragment_uses(self) -> None:
        for _ in range(50):
            assert 100_000_000 <= int(state_nonce()) <= 2_147_483_647
