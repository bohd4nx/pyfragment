"""Amounts and numbers as Fragment writes them."""

from decimal import Decimal

import pytest

from pyfragment.utils.money import numbers_in, parse_amount


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("0.4609", Decimal("0.4609")),
        ("1,000,000", Decimal("1000000")),
        (" 12 ", Decimal("12")),
        (5, Decimal("5")),
        (0, Decimal("0")),
    ],
)
def test_parse_amount_reads_fragment_formats(raw: object, expected: Decimal) -> None:
    assert parse_amount(raw) == expected


@pytest.mark.parametrize("raw", [None, True, "", "abc", "-1", "NaN", "Infinity"])
def test_parse_amount_rejects_what_is_not_a_non_negative_amount(raw: object) -> None:
    assert parse_amount(raw) is None


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("You can buy up to 10,000,000 stars", [10_000_000]),
        ("Enter amount from 50 to 10000000", [50, 10_000_000]),
        ("no numbers", []),
    ],
)
def test_numbers_in_drops_thousands_separators(text: str, expected: list[int]) -> None:
    assert numbers_in(text) == expected
