"""The account's Stars and Premium purchase history."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from pyfragment import FragmentClient, ParseError, PremiumHistoryEntry, StarsHistoryEntry
from pyfragment.constants.fragment import PREMIUM_HISTORY_PAGE, STARS_HISTORY_PAGE
from tests.support import fixtures
from tests.support.fake_fragment import FakeFragment

STARS_ROW = fixtures.html("stars_history.html")
STARS_CELL = '<div class="table-cell-value tm-value tm-nowrap">50</div>'
DATE = datetime(2026, 11, 24, 0, 43, 40, tzinfo=UTC)


def premium_page(*durations: str) -> str:
    """The real Stars history page, its row repeated once per duration with the "Duration" cell in place of "Stars"."""
    head, rest = STARS_ROW.split("<tbody>")
    row = rest.split("</tbody>")[0]
    rows = "".join(row.replace(STARS_CELL, f'<div class="tm-nowrap">{d}</div>') for d in durations)
    return f"{head}<tbody>{rows}</tbody></table>"


class TestGetStarsHistory:
    async def test_purchases_of_the_page(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.page(STARS_HISTORY_PAGE, STARS_ROW)

        entries = await client.get_stars_history()

        assert entries == [StarsHistoryEntry(username="example", name="@example", stars=50, gram=Decimal("0.7637"), date=DATE)]

    @pytest.mark.parametrize(("newest_first", "url"), [(True, STARS_HISTORY_PAGE), (False, f"{STARS_HISTORY_PAGE}?sort=asc")])
    async def test_order_picks_the_page_url(
        self, client: FragmentClient, fragment: FakeFragment, newest_first: bool, url: str
    ) -> None:
        fragment.page(url, STARS_ROW)

        await client.get_stars_history(newest_first=newest_first)

        assert fragment.fetched == [url]

    async def test_recipient_shown_by_name_only_is_kept(self, client: FragmentClient, fragment: FakeFragment) -> None:
        name_only = '<span class="tm-inline-nowrap accent-color">Bob &amp; Co</span>'
        link = '<a href="https://t.me/example" target="_blank" class="tm-inline-nowrap">@example</a>'
        fragment.page(STARS_HISTORY_PAGE, STARS_ROW.replace(link, name_only))

        [entry] = await client.get_stars_history()

        assert (entry.username, entry.name, entry.stars) == (None, "Bob & Co", 50)

    async def test_account_without_purchases(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.page(STARS_HISTORY_PAGE, "<html></html>")

        assert await client.get_stars_history() == []

    async def test_unreadable_amount_is_a_parse_error(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.page(STARS_HISTORY_PAGE, STARS_ROW.replace(">50</div>", ">lots</div>"))

        with pytest.raises(ParseError):
            await client.get_stars_history()


class TestGetPremiumHistory:
    async def test_gifts_with_their_duration_in_months(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.page(PREMIUM_HISTORY_PAGE, premium_page("6 months", "1 year"))

        entries = await client.get_premium_history()

        assert all(isinstance(entry, PremiumHistoryEntry) for entry in entries)
        assert [(e.username, e.months, e.gram, e.date) for e in entries] == [
            ("example", 6, Decimal("0.7637"), DATE),
            ("example", 12, Decimal("0.7637"), DATE),
        ]

    @pytest.mark.parametrize(
        ("newest_first", "url"), [(True, PREMIUM_HISTORY_PAGE), (False, f"{PREMIUM_HISTORY_PAGE}?sort=asc")]
    )
    async def test_order_picks_the_page_url(
        self, client: FragmentClient, fragment: FakeFragment, newest_first: bool, url: str
    ) -> None:
        fragment.page(url, premium_page("3 months"))

        await client.get_premium_history(newest_first=newest_first)

        assert fragment.fetched == [url]

    async def test_account_without_gifts(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.page(PREMIUM_HISTORY_PAGE, fixtures.html("premium_history_empty.html"))

        assert await client.get_premium_history() == []

    async def test_unknown_duration_is_a_parse_error(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.page(PREMIUM_HISTORY_PAGE, premium_page("forever"))

        with pytest.raises(ParseError):
            await client.get_premium_history()
