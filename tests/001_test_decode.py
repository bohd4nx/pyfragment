"""Read Fragment's BOC payloads: decode them, and find the payment comment in text and USDT (jetton) transfers."""

import re

import pytest
from ton_core import Cell

from pyfragment import ParseError
from pyfragment.utils.ton import body_comment, decode_boc
from tests.shared import fixture_json

PAYLOAD_CASES = [
    pytest.param(
        "te6ccgEBAgEALwABTgAAAAAxMDAwMDAwIFRlbGVncmFtIFN0YXJzIAoKUmVmI1RQb01wegEABkM3ZQ",
        id="stars",
    ),
    pytest.param(
        "te6ccgEBAgEANAABTgAAAABUZWxlZ3JhbSBQcmVtaXVtIGZvciAxIHllYXIgCgpSZWYjcgEAEE9OQnM2cmNt",
        id="premium",
    ),
    pytest.param(
        "te6ccgEBAgEAMAABTgAAAABUZWxlZ3JhbSBhY2NvdW50IHRvcCB1cCAKClJlZiNrMXpDRQEACFkxd3g",
        id="topup",
    ),
    pytest.param(
        "te6ccgEBAgEAfgABqA-KfqVP885dhccidjC3GwgBCkiH8LM_zUu0afyGCTWJwX1mDjdlf2rMa9UoQlD4UHUAF1jLlcMomlo5RJTwl8jnDDdfdhc7EgQQWPqFQ9IjyLPCAwEASgAAAAA1MCBUZWxlZ3JhbSBTdGFycyAKClJlZiNtOUpoWndBcFE",
        id="real_stars_50",
    ),
    pytest.param(
        "te6ccgEBAgEANgABTgAAAABUZWxlZ3JhbSBQcmVtaXVtIGZvciAzIG1vbnRocyAKClJlZgEAFCMzcFdKdGJkYnU",
        id="real_premium_3m",
    ),
    pytest.param(
        "te6ccgEBAwEAhgABqg-KfqWibdDaYaJCPUWWgvAIAQpIh_CzP81LtGn8hgk1icF9Zg43ZX9qzGvVKEJQ-FB1ABdYy5XDKJpaOUSU8JfI5ww3X3YXOxIEEFj6hUPSI8izwgMBAU4AAAAAMTAwMDAwIFRlbGVncmFtIFN0YXJzIAoKUmVmIzBoZ0RmNEYCAAQ5VA",
        id="real_stars_100k",
    ),
]


# Real payloads: plain text comments and USDT jetton transfers carrying one


@pytest.mark.parametrize("payload", PAYLOAD_CASES)
def test_every_real_payload_carries_its_payment_comment(payload: str) -> None:
    comment = body_comment(decode_boc(payload))
    assert comment is not None and re.fullmatch(r"[^\n]*Telegram[^\n]* \n\nRef#[A-Za-z0-9]+", comment), comment


def test_comment_from_real_stars_link_response() -> None:
    message = fixture_json("stars_transaction_link_response.json")["transaction"]["messages"][0]
    assert body_comment(decode_boc(message["payload"])) == "50 Telegram Stars \n\nRef#kpJ55h3BW"


# decode_boc


def test_empty_payload_is_none() -> None:
    assert decode_boc("") is None and decode_boc(None) is None


def test_invalid_payload_raises_parse_error() -> None:
    with pytest.raises(ParseError):
        decode_boc("!!!not-valid-base64!!!")


def test_base64url_and_standard_base64_decode_alike() -> None:
    payload = "te6ccgEBAQEAJwAASgAAAAA1MCBUZWxlZ3JhbSBTdGFycyAKClJlZiNrcEo1NWgzQlc="
    url_form = payload.replace("+", "-").replace("/", "_").rstrip("=")
    cell = decode_boc(payload)
    assert isinstance(cell, Cell) and cell.hash == decode_boc(url_form).hash  # type: ignore[union-attr]


# body_comment


def test_body_without_a_comment_has_none() -> None:
    assert body_comment(None) is None
    assert body_comment(Cell.empty()) is None
