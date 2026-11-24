"""Reading the purchase tables of fragment.com/stars/history and /premium/history."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from pyfragment import ParseError
from pyfragment.domains.history.parser import HistoryRow, parse_history_rows, parse_months, parse_stars
from tests.support import fixtures

STARS_PAGE_HTML = fixtures.html("stars_history.html")
USER_LINK = '<a href="https://t.me/example" target="_blank" class="tm-inline-nowrap">@example</a>'
STARS_CELL = '<div class="table-cell-value tm-value tm-nowrap">50</div>'
PRICE_CELL = '<div class="table-cell-value tm-value icon-before icon-ton">0<span class="mini-frac">.7637</span></div>'


def page_with(old: str, new: str) -> str:
    """The real Stars history page with one of its cells swapped."""
    assert old in STARS_PAGE_HTML
    return STARS_PAGE_HTML.replace(old, new)


def premium_page(duration: str) -> str:
    """A Premium history row: it is the Stars row with a "Duration" cell."""
    return page_with(STARS_CELL, f'<div class="tm-nowrap">{duration}</div>')


class TestParseHistoryRows:
    def test_row_of_the_real_page(self) -> None:
        assert parse_history_rows(STARS_PAGE_HTML) == [
            HistoryRow(
                username="example",
                name="@example",
                quantity="50",
                gram=Decimal("0.7637"),
                date=datetime(2026, 11, 24, 0, 43, 40, tzinfo=UTC),
            )
        ]

    def test_header_row_is_not_a_purchase(self) -> None:
        assert "<th" in STARS_PAGE_HTML
        assert len(parse_history_rows(STARS_PAGE_HTML)) == 1

    def test_page_without_a_table(self) -> None:
        assert parse_history_rows(fixtures.html("premium_history_empty.html")) == []

    def test_recipient_shown_by_name_only_has_no_username(self) -> None:
        name_only = '<span class="tm-inline-nowrap accent-color">Bob &amp; Co</span>'

        [row] = parse_history_rows(page_with(USER_LINK, name_only))

        assert (row.username, row.name) == (None, "Bob & Co")

    def test_price_without_a_fraction(self) -> None:
        [row] = parse_history_rows(page_with(PRICE_CELL, '<div class="icon-ton">1</div>'))

        assert row.gram == Decimal("1")

    def test_premium_duration_cell_is_the_quantity(self) -> None:
        [row] = parse_history_rows(premium_page("6 months"))

        assert row.quantity == "6 months"

    @pytest.mark.parametrize("cell", [USER_LINK, STARS_CELL, PRICE_CELL, '<time datetime="2026-11-24T00:43:40+00:00"'])
    def test_row_missing_a_cell_is_an_error_not_a_dropped_purchase(self, cell: str) -> None:
        page = STARS_PAGE_HTML.replace(cell, "") if cell != USER_LINK else page_with(USER_LINK, "")

        with pytest.raises(ParseError, match="unrecognised row"):
            parse_history_rows(page)


class TestParseStars:
    @pytest.mark.parametrize(("cell", "stars"), [("50", 50), ("1,500", 1500), ("10,000,000", 10_000_000)])
    def test_amount_with_thousands_separators(self, cell: str, stars: int) -> None:
        assert parse_stars(cell) == stars

    def test_unreadable_amount(self) -> None:
        with pytest.raises(ParseError, match="lots"):
            parse_stars("lots")


class TestParseMonths:
    @pytest.mark.parametrize(
        ("cell", "months"),
        [("1 month", 1), ("3 months", 3), ("6 months", 6), ("1 year", 12), ("2 years", 24)],
    )
    def test_duration_in_months(self, cell: str, months: int) -> None:
        assert parse_months(cell) == months

    @pytest.mark.parametrize("cell", ["forever", "", "6", "6 months!"])
    def test_unknown_duration(self, cell: str) -> None:
        with pytest.raises(ParseError, match="bad duration"):
            parse_months(cell)
