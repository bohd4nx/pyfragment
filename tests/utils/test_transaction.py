"""Reading the transaction Fragment asks the wallet to sign."""

import time
from typing import Any

import pytest
from ton_core import Address

from pyfragment import TransactionError
from pyfragment.constants.chain import MESSAGE_TTL
from pyfragment.utils.transaction import deadline, extract_message, parse_destination, signing_expiry, unsigned_int
from tests.support import fixtures

ADDRESS = "UQCFJEP4WZ_mpdo0_kMEmsTgvrMHG7K_tWY16pQhKHwoOtFz"


def link(**transaction: Any) -> dict[str, Any]:
    return {"transaction": transaction}


class TestExtractMessage:
    def test_the_single_message_of_a_real_link(self) -> None:
        message = extract_message(fixtures.response("stars_transaction_link.json"))
        assert message["address"] == ADDRESS and message["amount"] == "767600000"

    @pytest.mark.parametrize(
        "data", [{}, {"transaction": None}, {"transaction": {}}, link(messages=[]), link(messages="x"), link(messages={"a": 1})]
    )
    def test_missing_or_empty_messages_are_an_invalid_payload(self, data: dict[str, Any]) -> None:
        with pytest.raises(TransactionError, match="invalid transaction payload"):
            extract_message(data)

    def test_several_messages_are_refused_rather_than_partly_paid(self) -> None:
        with pytest.raises(TransactionError, match="2 messages"):
            extract_message(link(messages=[{"address": ADDRESS}, {"address": ADDRESS}]))


class TestUnsignedInt:
    @pytest.mark.parametrize(("raw", "expected"), [(0, 0), (5, 5), ("767600000", 767_600_000), ("0", 0)])
    def test_numbers_and_digit_strings(self, raw: object, expected: int) -> None:
        assert unsigned_int(raw) == expected

    @pytest.mark.parametrize("raw", [True, None, -1, 1.5, "-1", "1.5", "", "abc", [1]])
    def test_anything_else_is_an_invalid_payload(self, raw: object) -> None:
        with pytest.raises(TransactionError):
            unsigned_int(raw)


class TestParseDestination:
    def test_user_friendly_address(self) -> None:
        assert parse_destination({"address": ADDRESS}) == Address(ADDRESS)

    def test_a_domain_is_not_resolved(self) -> None:
        with pytest.raises(TransactionError):
            parse_destination({"address": "wallet.ton"})

    @pytest.mark.parametrize("message", [{}, {"address": ""}, {"address": "nope"}])
    def test_missing_or_malformed_address_is_an_invalid_payload(self, message: dict[str, Any]) -> None:
        with pytest.raises(TransactionError):
            parse_destination(message)


class TestDeadline:
    def test_none_when_fragment_states_none(self) -> None:
        assert deadline(link(messages=[])) is None

    def test_a_future_deadline_is_returned(self) -> None:
        future = int(time.time()) + 300
        assert deadline(link(validUntil=future)) == future
        assert deadline(link(validUntil=str(future))) == future

    def test_a_past_deadline_is_a_retryable_error(self) -> None:
        with pytest.raises(TransactionError, match="expired") as exc_info:
            deadline(link(validUntil=1))
        assert exc_info.value.retryable

    def test_the_real_link_has_long_expired(self) -> None:
        data = fixtures.response("stars_transaction_link.json")
        data["transaction"]["validUntil"] = 1_000
        with pytest.raises(TransactionError):
            deadline(data)

    def test_a_garbage_deadline_is_an_invalid_payload(self) -> None:
        with pytest.raises(TransactionError, match="invalid transaction payload"):
            deadline(link(validUntil="soon"))


class TestSigningExpiry:
    def test_default_is_the_message_ttl(self) -> None:
        assert signing_expiry([], 1_000.9) == 1_000 + MESSAGE_TTL
        assert signing_expiry([None, None], 1_000) == 1_000 + MESSAGE_TTL

    def test_the_earliest_deadline_wins(self) -> None:
        assert signing_expiry([None, 1_030, 1_050], 1_000) == 1_030

    def test_a_later_deadline_does_not_extend_it(self) -> None:
        assert signing_expiry([5_000], 1_000) == 1_000 + MESSAGE_TTL
