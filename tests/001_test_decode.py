"""Tests for clean_decode() — BOC-encoded Fragment payloads decode to UTF-8."""

import re

import pytest

from pyfragment.types import ParseError
from pyfragment.utils.decoder import clean_decode

PAYLOADS = [
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
]


@pytest.mark.parametrize("payload", PAYLOADS)
def test_decode_payload(payload: str) -> None:
    result = clean_decode(payload)
    assert "Telegram" in result
    assert re.search(r"Ref#[A-Za-z0-9]+", result), f"no Ref# in {result!r}"
    assert all(ord(c) < 128 for c in result), f"non-ASCII chars in {result!r}"


def test_empty_payload_returns_empty_string() -> None:
    assert clean_decode("") == ""


def test_invalid_payload_raises_parse_error() -> None:
    with pytest.raises(ParseError):
        clean_decode("!!!not-valid-base64!!!")
