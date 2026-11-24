"""Parse Fragment response bodies with the typed schemas."""

import pytest

from pyfragment.enums import StateMode
from pyfragment.schemas import InvoiceRequest, PageState, RecipientSearch, TransactionLink
from tests.shared import FAKE_CONFIRM_METHOD, fixture_json

# RecipientSearch


def test_recipient_search_found() -> None:
    assert RecipientSearch.from_response({"found": {"recipient": "token"}}).recipient == "token"


@pytest.mark.parametrize("response", [{}, {"found": {}}, {"found": None}, {"found": "oops"}, {"found": {"recipient": ""}}])
def test_recipient_search_missing(response: dict[str, object]) -> None:
    assert RecipientSearch.from_response(response).recipient is None


# InvoiceRequest


def test_invoice_request_parses_id() -> None:
    assert InvoiceRequest.from_response({"req_id": "r1"}).req_id == "r1"


def test_invoice_request_missing_fields() -> None:
    assert InvoiceRequest.from_response({"error": "nope"}).req_id is None


# TransactionLink


def test_transaction_link_defaults() -> None:
    link = TransactionLink.from_response({})
    assert (link.need_verify, link.confirm_method, link.confirm_params) == (False, None, {})


def test_transaction_link_reads_confirm_details() -> None:
    link = TransactionLink.from_response(
        {"need_verify": True, "confirm_method": FAKE_CONFIRM_METHOD, "confirm_params": {"id": "r1"}}
    )
    assert (link.need_verify, link.confirm_method, link.confirm_params) == (True, FAKE_CONFIRM_METHOD, {"id": "r1"})


# PageState


def test_page_state_done_when_no_update_needed() -> None:
    state = PageState.from_response({"mode": "done", "need_update": False})
    assert state.is_done and state.mode == StateMode.DONE


def test_page_state_not_done_by_default() -> None:
    state = PageState.from_response({})
    assert not state.is_done and state.mode == StateMode.NEW


def test_page_state_keeps_the_previous_mode_when_response_has_none() -> None:
    assert PageState.from_response({"need_update": True}, default_mode=StateMode.PROCESSING).mode == "processing"


# Real Fragment responses (tests/fixtures)


def test_invoice_request_from_real_init_response() -> None:
    invoice = InvoiceRequest.from_response(fixture_json("stars_invoice_response.json"))

    assert invoice.req_id == "REQ_ID"


def test_transaction_link_from_real_link_response() -> None:
    link = TransactionLink.from_response(fixture_json("stars_transaction_link_response.json"))

    assert (link.need_verify, link.confirm_method, link.confirm_params) == (False, FAKE_CONFIRM_METHOD, {"id": "REQ_ID"})
