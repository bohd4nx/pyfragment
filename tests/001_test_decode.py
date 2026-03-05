"""Tests for clean_decode() — BOC-encoded Fragment payloads decode to
human-readable UTF-8 with the Telegram label and Ref# intact."""
import re

import pytest

from app.utils.decoder import clean_decode

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
def test_payload(payload: str) -> None:
    result = clean_decode(payload)
    assert "Telegram" in result
    assert re.search(r"Ref#[A-Za-z0-9]+", result), f"no Ref# in {result!r}"
    assert all(ord(c) <= 127 for c in result), f"non-ASCII chars in {result!r}"


def test_empty_input_returns_string() -> None:
    assert isinstance(clean_decode(""), str)
