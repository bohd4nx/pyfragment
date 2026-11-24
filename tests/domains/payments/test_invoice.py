"""Opening an invoice and requesting the transaction that pays it."""

import pytest

from pyfragment import (
    AlreadySubscribedError,
    FragmentAPIError,
    FragmentClient,
    InvoiceExpiredError,
    SessionExpiredError,
    VerificationError,
)
from pyfragment.constants.chain import DEVICE_INFO
from pyfragment.domains.payments.flow import PurchaseFlow
from pyfragment.domains.payments.invoice import create_invoice, request_transaction, wallet_fields
from pyfragment.enums import ApiError, ApiMethod
from tests.support import fixtures
from tests.support.data import ACCOUNT, REQ_ID
from tests.support.fake_fragment import FakeFragment

FLOW = PurchaseFlow(
    search_method=ApiMethod.SEARCH_STARS_RECIPIENT,
    page_url="https://fragment.com/stars/buy",
    state_method=ApiMethod.UPDATE_STARS_BUY_STATE,
    init_method=ApiMethod.INIT_BUY_STARS_REQUEST,
    link_method=ApiMethod.GET_BUY_STARS_LINK,
    label="Test purchase",
)


class TestWalletFields:
    def test_account_and_device_are_sent_as_json_strings(self) -> None:
        import json

        fields = wallet_fields(ACCOUNT)
        assert json.loads(fields["account"]) == ACCOUNT
        assert json.loads(fields["device"]) == DEVICE_INFO


class TestCreateInvoice:
    async def test_returns_the_request_id_and_sends_the_init_data(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(FLOW.init_method, fixtures.response("stars_invoice.json"))

        assert await create_invoice(client, FLOW, {"recipient": "r", "quantity": 50}) == REQ_ID
        assert fragment.calls[0].data == {"recipient": "r", "quantity": 50}
        assert fragment.calls[0].page_url == FLOW.page_url

    async def test_need_ton_is_a_session_error_naming_the_flow(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(FLOW.init_method, {"need_ton": True})

        with pytest.raises(SessionExpiredError, match="stel_ton_token") as exc_info:
            await create_invoice(client, FLOW, {})
        assert FLOW.label in str(exc_info.value)

    async def test_already_subscribed_recipient(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(FLOW.init_method, fixtures.response("premium_recipient_already_subscribed.json"))

        with pytest.raises(AlreadySubscribedError):
            await create_invoice(client, FLOW, {})

    async def test_an_error_answer_without_a_request_id_is_raised(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(FLOW.init_method, fixtures.response("stars_below_minimum.json"))

        with pytest.raises(FragmentAPIError, match="minimum"):
            await create_invoice(client, FLOW, {})

    async def test_an_answer_with_neither_id_nor_error_is_a_session_error(
        self, client: FragmentClient, fragment: FakeFragment
    ) -> None:
        fragment.reply(FLOW.init_method, {"ok": True})

        with pytest.raises(SessionExpiredError) as exc_info:
            await create_invoice(client, FLOW, {})
        assert FLOW.label in str(exc_info.value)


class TestRequestTransaction:
    async def test_returns_fragments_transaction_and_asks_for_it_by_request_id(
        self, client: FragmentClient, fragment: FakeFragment
    ) -> None:
        link = fixtures.response("stars_transaction_link.json")
        fragment.reply(FLOW.link_method, link)

        assert await request_transaction(client, FLOW, REQ_ID, {"show_sender": 0}) == link
        assert fragment.calls[0].data == {"transaction": 1, "id": REQ_ID, "show_sender": 0}
        assert fragment.calls[0].page_url == FLOW.page_url

    async def test_link_data_is_optional(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(FLOW.link_method, fixtures.response("stars_transaction_link.json"))

        await request_transaction(client, FLOW, REQ_ID, None)
        assert fragment.calls[0].data == {"transaction": 1, "id": REQ_ID}

    async def test_need_verify_is_a_verification_error(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(FLOW.link_method, {"need_verify": True, "confirm_method": "checkVerify"})

        with pytest.raises(VerificationError):
            await request_transaction(client, FLOW, REQ_ID, None)

    async def test_expired_invoice_is_retryable_and_names_the_flow(
        self, client: FragmentClient, fragment: FakeFragment
    ) -> None:
        fragment.reply(FLOW.link_method, {"error": ApiError.INVOICE_EXPIRED.capitalize()})

        with pytest.raises(InvoiceExpiredError) as exc_info:
            await request_transaction(client, FLOW, REQ_ID, None)
        assert exc_info.value.retryable
        assert FLOW.label in str(exc_info.value)

    async def test_any_other_error_is_raised_as_it_is(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(FLOW.link_method, {"error": "Something new"})

        with pytest.raises(FragmentAPIError, match="Something new"):
            await request_transaction(client, FLOW, REQ_ID, None)
