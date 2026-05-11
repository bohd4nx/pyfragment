"""Tests for clean_decode() — TON BOC payload decoding."""

import base64
import re
from unittest.mock import patch

import pytest
from ton_core import Cell

from pyfragment.types import ParseError
from pyfragment.utils.wallet.transaction import clean_decode

PAYLOAD_CASES = [
    pytest.param(
        "te6ccgEBAgEALwABTgAAAAAxMDAwMDAwIFRlbGVncmFtIFN0YXJzIAoKUmVmI1RQb01wegEABkM3ZQ",
        True,
        id="stars",
    ),
    pytest.param(
        "te6ccgEBAgEANAABTgAAAABUZWxlZ3JhbSBQcmVtaXVtIGZvciAxIHllYXIgCgpSZWYjcgEAEE9OQnM2cmNt",
        True,
        id="premium",
    ),
    pytest.param(
        "te6ccgEBAgEAMAABTgAAAABUZWxlZ3JhbSBhY2NvdW50IHRvcCB1cCAKClJlZiNrMXpDRQEACFkxd3g",
        True,
        id="topup",
    ),
    pytest.param(
        "te6ccgEBAgEAfgABqA-KfqVP885dhccidjC3GwgBCkiH8LM_zUu0afyGCTWJwX1mDjdlf2rMa9UoQlD4UHUAF1jLlcMomlo5RJTwl8jnDDdfdhc7EgQQWPqFQ9IjyLPCAwEASgAAAAA1MCBUZWxlZ3JhbSBTdGFycyAKClJlZiNtOUpoWndBcFE",
        False,
        id="real_stars_50",
    ),
    pytest.param(
        "te6ccgEBAgEANgABTgAAAABUZWxlZ3JhbSBQcmVtaXVtIGZvciAzIG1vbnRocyAKClJlZgEAFCMzcFdKdGJkYnU",
        False,
        id="real_premium_3m",
    ),
    pytest.param(
        "te6ccgEBAwEAhgABqg-KfqWibdDaYaJCPUWWgvAIAQpIh_CzP81LtGn8hgk1icF9Zg43ZX9qzGvVKEJQ-FB1ABdYy5XDKJpaOUSU8JfI5ww3X3YXOxIEEFj6hUPSI8izwgMBAU4AAAAAMTAwMDAwIFRlbGVncmFtIFN0YXJzIAoKUmVmIzBoZ0RmNEYCAAQ5VA",
        False,
        id="real_stars_100k",
    ),
]


# Decode valid payload tests


@pytest.mark.parametrize(("payload", "strict_ref"), PAYLOAD_CASES)
def test_decode_payload(payload: str, strict_ref: bool) -> None:
    result = clean_decode(payload)
    if isinstance(result, str):
        assert "Telegram" in result
        if strict_ref:
            assert re.search(r"Ref#[A-Za-z0-9]+", result), f"no Ref# in {result!r}"
        assert all(ord(c) < 128 for c in result), f"non-ASCII chars in {result!r}"
    else:
        assert isinstance(result, Cell)


# Edge case tests


def test_empty_payload_returns_empty_string() -> None:
    assert clean_decode("") == ""


def test_invalid_payload_raises_parse_error() -> None:
    with pytest.raises(ParseError):
        clean_decode("!!!not-valid-base64!!!")


def test_decode_payload_accepts_base64url_alphabet() -> None:
    class _FakeSlice:
        def load_uint(self, _: int) -> int:
            return 0

        def load_snake_string(self) -> str:
            return "Telegram Stars Ref#abc"

    class _FakeCell:
        def begin_parse(self) -> _FakeSlice:
            return _FakeSlice()

    raw = b"\xfb\xef\xff\x00"
    payload = base64.urlsafe_b64encode(raw).decode().rstrip("=")

    with patch("pyfragment.utils.wallet.transaction.Cell.one_from_boc", return_value=_FakeCell()) as mocked:
        result = clean_decode(payload)

    mocked.assert_called_once_with(raw)
    assert result == "Telegram Stars Ref#abc"


def test_clean_decode_returns_text_comment_when_utf8() -> None:
    class _FakeSlice:
        def load_uint(self, _: int) -> int:
            return 0

        def load_snake_string(self) -> str:
            return "Telegram Premium Ref#abc"

    class _FakeCell:
        def begin_parse(self) -> _FakeSlice:
            return _FakeSlice()

    payload = base64.urlsafe_b64encode(b"\x00\x01").decode().rstrip("=")
    with patch("pyfragment.utils.wallet.transaction.Cell.one_from_boc", return_value=_FakeCell()):
        parsed = clean_decode(payload)

    assert parsed == "Telegram Premium Ref#abc"


def test_clean_decode_returns_cell_for_binary_payload() -> None:
    class _FakeSlice:
        def load_uint(self, _: int) -> int:
            return 0

        def load_snake_string(self) -> str:
            raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")

    class _FakeCell:
        def begin_parse(self) -> _FakeSlice:
            return _FakeSlice()

    payload = base64.urlsafe_b64encode(b"\x00\x01").decode().rstrip("=")
    fake_cell: object = _FakeCell()
    with patch("pyfragment.utils.wallet.transaction.Cell.one_from_boc", return_value=fake_cell):
        parsed = clean_decode(payload)

    assert parsed is fake_cell
