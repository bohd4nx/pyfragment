"""Parse Fragment response bodies with the typed schemas and match known error messages."""

import pytest

from pyfragment.enums import ApiError, StateMode
from pyfragment.schemas import InvoiceRequest, PageState, RecipientSearch, TransactionLink, error_text, has_error

# error_text / has_error


def test_error_text_none_on_success() -> None:
    assert error_text({"ok": True}) is None
    assert error_text({"error": ""}) is None


def test_error_text_returns_message() -> None:
    assert error_text({"error": "Bad request"}) == "Bad request"


@pytest.mark.parametrize(
    ("message", "error"),
    [
        ("Please enter a username assigned to a user.", ApiError.NOT_A_USER),
        ("This account is already subscribed to Telegram Premium.", ApiError.ALREADY_SUBSCRIBED),
        ("Bad request", ApiError.BAD_REQUEST),
        ("bad REQUEST", ApiError.BAD_REQUEST),
        ("Invalid method", ApiError.INVALID_METHOD),
        ("Access denied", ApiError.ACCESS_DENIED),
    ],
)
def test_has_error_matches_known_messages_case_insensitively(message: str, error: ApiError) -> None:
    assert has_error({"error": message}, error)


def test_has_error_false_for_other_or_missing_errors() -> None:
    assert not has_error({"error": "Something else"}, ApiError.BAD_REQUEST)
    assert not has_error({}, ApiError.BAD_REQUEST)


# RecipientSearch


def test_recipient_search_found() -> None:
    assert RecipientSearch.from_response({"found": {"recipient": "token"}}).recipient == "token"


@pytest.mark.parametrize("response", [{}, {"found": {}}, {"found": None}, {"found": "oops"}, {"found": {"recipient": ""}}])
def test_recipient_search_missing(response: dict[str, object]) -> None:
    assert RecipientSearch.from_response(response).recipient is None


# InvoiceRequest


def test_invoice_request_parses_id_and_amount() -> None:
    invoice = InvoiceRequest.from_response({"req_id": "r1", "amount": "1,000.5"})
    assert (invoice.req_id, invoice.amount) == ("r1", 1000.5)


@pytest.mark.parametrize(
    ("raw_amount", "expected"),
    [("0.326", 0.326), ("0.00075", 0.00075), ("1,000,000,000", 1_000_000_000.0), (None, None), ("n/a", None)],
)
def test_invoice_request_amount_parsing(raw_amount: str | None, expected: float | None) -> None:
    assert InvoiceRequest.from_response({"req_id": "r1", "amount": raw_amount}).amount == expected


def test_invoice_request_missing_fields() -> None:
    invoice = InvoiceRequest.from_response({"error": "nope"})
    assert (invoice.req_id, invoice.amount) == (None, None)


# TransactionLink


def test_transaction_link_defaults() -> None:
    link = TransactionLink.from_response({})
    assert (link.need_verify, link.confirm_method, link.confirm_params) == (False, None, {})


def test_transaction_link_reads_confirm_details() -> None:
    link = TransactionLink.from_response({"need_verify": True, "confirm_method": "confirmReq", "confirm_params": {"id": "r1"}})
    assert (link.need_verify, link.confirm_method, link.confirm_params) == (True, "confirmReq", {"id": "r1"})


# PageState


def test_page_state_done_when_no_update_needed() -> None:
    state = PageState.from_response({"mode": "done", "need_update": False})
    assert state.is_done and state.mode == StateMode.DONE


def test_page_state_not_done_by_default() -> None:
    state = PageState.from_response({})
    assert not state.is_done and state.mode == StateMode.NEW


def test_page_state_keeps_the_previous_mode_when_response_has_none() -> None:
    assert PageState.from_response({"need_update": True}, default_mode=StateMode.PROCESSING).mode == "processing"
