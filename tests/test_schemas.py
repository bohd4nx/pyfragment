"""The typed views over Fragment's init/link/state responses."""

import pytest

from pyfragment.enums import StateMode
from pyfragment.schemas import InvoiceRequest, PageState, RecipientSearch, TransactionLink
from tests.support import fixtures
from tests.support.data import RECIPIENT_TOKEN, REQ_ID


class TestRecipientSearch:
    def test_a_found_recipient_from_a_real_response(self) -> None:
        found = RecipientSearch.from_response(fixtures.response("stars_recipient_found.json"))

        assert found.recipient == RECIPIENT_TOKEN
        assert found.myself is False
        assert found.photo and found.photo.startswith("<img")

    def test_only_the_token_is_required(self) -> None:
        assert RecipientSearch.from_response({"found": {"recipient": "t"}}) == RecipientSearch(recipient="t")

    @pytest.mark.parametrize(
        "response",
        [
            {},
            {"found": {}},
            {"found": None},
            {"found": "oops"},
            {"found": []},
            {"found": {"recipient": ""}},
            fixtures.response("stars_recipient_not_found.json"),
        ],
    )
    def test_no_recipient_when_nothing_usable_was_found(self, response: dict[str, object]) -> None:
        assert RecipientSearch.from_response(response).recipient is None

    def test_the_html_escaped_name_is_unescaped(self) -> None:
        response = {"found": {"recipient": "t", "name": "Pavel &amp; Co &lt;3"}}

        assert RecipientSearch.from_response(response).name == "Pavel & Co <3"

    @pytest.mark.parametrize("name", ["", None])
    def test_an_empty_name_is_none(self, name: str | None) -> None:
        assert RecipientSearch.from_response({"found": {"recipient": "t", "name": name}}).name is None

    def test_photo_and_myself_are_read(self) -> None:
        response = {"found": {"recipient": "t", "photo": "<img src='x'>", "myself": 1}}

        search = RecipientSearch.from_response(response)

        assert search.photo == "<img src='x'>" and search.myself is True

    def test_is_immutable(self) -> None:
        with pytest.raises(AttributeError):
            RecipientSearch(recipient="t").recipient = "u"  # type: ignore[misc]


class TestInvoiceRequest:
    def test_reads_the_id_from_a_real_response(self) -> None:
        assert InvoiceRequest.from_response(fixtures.response("stars_invoice.json")).req_id == REQ_ID

    @pytest.mark.parametrize("response", [{"error": "nope"}, {}, {"req_id": ""}, {"req_id": None}])
    def test_no_id_when_fragment_gave_none(self, response: dict[str, object]) -> None:
        assert InvoiceRequest.from_response(response).req_id is None


class TestTransactionLink:
    def test_defaults_for_an_empty_response(self) -> None:
        link = TransactionLink.from_response({})

        assert (link.need_verify, link.confirm_method, link.confirm_params) == (False, None, {})

    def test_reads_the_confirm_details_from_a_real_response(self) -> None:
        link = TransactionLink.from_response(fixtures.response("stars_transaction_link.json"))

        assert (link.need_verify, link.confirm_method, link.confirm_params) == (False, "confirmReq", {"id": REQ_ID})

    def test_need_verify_is_read(self) -> None:
        assert TransactionLink.from_response({"need_verify": True}).need_verify is True

    @pytest.mark.parametrize("response", [{"confirm_method": "", "confirm_params": None}, {"confirm_params": {}}])
    def test_empty_values_are_normalised(self, response: dict[str, object]) -> None:
        link = TransactionLink.from_response(response)

        assert link.confirm_method is None and link.confirm_params == {}

    def test_default_params_are_not_shared_between_instances(self) -> None:
        assert TransactionLink(False, None).confirm_params is not TransactionLink(False, None).confirm_params


class TestPageState:
    def test_done_when_no_update_is_needed(self) -> None:
        state = PageState.from_response({"mode": StateMode.DONE, "need_update": False})

        assert state.is_done and state.mode == StateMode.DONE

    def test_not_done_by_default(self) -> None:
        state = PageState.from_response({})

        assert not state.is_done and state.mode == StateMode.NEW and state.need_update

    def test_the_default_mode_applies_when_the_response_has_none(self) -> None:
        assert PageState.from_response({"need_update": True}, default_mode=StateMode.PROCESSING).mode == StateMode.PROCESSING

    def test_the_response_mode_wins_over_the_default(self) -> None:
        assert PageState.from_response({"mode": StateMode.DONE}, default_mode=StateMode.PROCESSING).mode == StateMode.DONE
