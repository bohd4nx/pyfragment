"""Reading Fragment's BOC payloads: decoding, and finding the payment comment in text and USDT (jetton) transfers."""

import re

import pytest
from ton_core import Address, Cell, begin_cell

from pyfragment import ParseError
from pyfragment.utils.ton import body_comment, decode_boc
from tests.support import fixtures

REAL_PAYLOADS = [
    pytest.param("te6ccgEBAgEALwABTgAAAAAxMDAwMDAwIFRlbGVncmFtIFN0YXJzIAoKUmVmI1RQb01wegEABkM3ZQ", id="stars"),
    pytest.param("te6ccgEBAgEANAABTgAAAABUZWxlZ3JhbSBQcmVtaXVtIGZvciAxIHllYXIgCgpSZWYjcgEAEE9OQnM2cmNt", id="premium"),
    pytest.param("te6ccgEBAgEAMAABTgAAAABUZWxlZ3JhbSBhY2NvdW50IHRvcCB1cCAKClJlZiNrMXpDRQEACFkxd3g", id="topup"),
    pytest.param(
        "te6ccgEBAgEAfgABqA-KfqVP885dhccidjC3GwgBCkiH8LM_zUu0afyGCTWJwX1mDjdlf2rMa9UoQlD4UHUAF1jLlcMomlo5RJTwl8jnDDdfdhc7EgQQWPqFQ9IjyLPCAwEASgAAAAA1MCBUZWxlZ3JhbSBTdGFycyAKClJlZiNtOUpoWndBcFE",
        id="usdt_stars_50",
    ),
    pytest.param(
        "te6ccgEBAwEAhgABqg-KfqWibdDaYaJCPUWWgvAIAQpIh_CzP81LtGn8hgk1icF9Zg43ZX9qzGvVKEJQ-FB1ABdYy5XDKJpaOUSU8JfI5ww3X3YXOxIEEFj6hUPSI8izwgMBAU4AAAAAMTAwMDAwIFRlbGVncmFtIFN0YXJzIAoKUmVmIzBoZ0RmNEYCAAQ5VA",
        id="usdt_stars_100k",
    ),
]


class TestDecodeBoc:
    def test_nothing_to_decode_is_none(self) -> None:
        assert decode_boc("") is None and decode_boc(None) is None and decode_boc("  ") is None

    def test_garbage_is_a_parse_error(self) -> None:
        with pytest.raises(ParseError):
            decode_boc("!!!not-valid-base64!!!")

    def test_base64url_without_padding_decodes_like_standard_base64(self) -> None:
        payload = "te6ccgEBAQEAJwAASgAAAAA1MCBUZWxlZ3JhbSBTdGFycyAKClJlZiNrcEo1NWgzQlc="
        url_form = payload.replace("+", "-").replace("/", "_").rstrip("=")
        standard, url = decode_boc(payload), decode_boc(url_form)
        assert isinstance(standard, Cell) and url is not None and standard.hash == url.hash


class TestBodyComment:
    def test_no_body_or_an_empty_one_has_no_comment(self) -> None:
        assert body_comment(None) is None
        assert body_comment(Cell.empty()) is None

    def test_real_stars_link_payload(self) -> None:
        message = fixtures.response("stars_transaction_link.json")["transaction"]["messages"][0]
        assert body_comment(decode_boc(message["payload"])) == "50 Telegram Stars \n\nRef#nd7jvgt6H"

    @pytest.mark.parametrize("payload", REAL_PAYLOADS)
    def test_real_payloads_carry_the_payment_reference(self, payload: str) -> None:
        comment = body_comment(decode_boc(payload))
        assert comment is not None and re.fullmatch(r"[^\n]*Telegram[^\n]* \n\nRef#[A-Za-z0-9]+", comment), comment

    def test_non_text_opcode_has_no_comment(self) -> None:
        assert body_comment(begin_cell().store_uint(0x12345678, 32).store_uint(0, 8).end_cell()) is None

    def test_jetton_transfer_with_inline_forward_payload(self) -> None:
        body = jetton_transfer(inline=True)
        assert body_comment(body) == "hello"

    def test_jetton_transfer_with_forward_payload_in_a_ref(self) -> None:
        assert body_comment(jetton_transfer(inline=False)) == "hello"

    def test_malformed_jetton_transfer_has_no_comment(self) -> None:
        assert body_comment(begin_cell().store_uint(0x0F8A7EA5, 32).store_uint(0, 64).end_cell()) is None


def jetton_transfer(*, inline: bool) -> Cell:
    comment = begin_cell().store_uint(0, 32).store_snake_string("hello").end_cell()
    address = Address("UQCFJEP4WZ_mpdo0_kMEmsTgvrMHG7K_tWY16pQhKHwoOtFz")
    builder = (
        begin_cell()
        .store_uint(0x0F8A7EA5, 32)
        .store_uint(0, 64)
        .store_coins(1)
        .store_address(address)
        .store_address(address)
        .store_bit(0)
        .store_coins(1)
    )
    if inline:
        builder.store_bit(0).store_uint(0, 32).store_snake_string("hello")
    else:
        builder.store_bit(1).store_ref(comment)
    return builder.end_cell()
