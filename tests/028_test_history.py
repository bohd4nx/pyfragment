"""Tests for get_stars_history and get_premium_history (rows shaped like fragment.com/*/history, names made up)."""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from pyfragment import FragmentClient, ParseError, PremiumHistoryEntry, StarsHistoryEntry
from pyfragment.constants.fragment import PREMIUM_HISTORY_PAGE, STARS_HISTORY_PAGE


def row(recipient: str, quantity: str, price: str, when: str, quantity_class: str) -> str:
    return f"""<tr>
    <td><div class="table-cell">{recipient}</div></td>
    <td><div class="table-cell"><div class="{quantity_class}">{quantity}</div></div></td>
    <td><div class="table-cell"><div class="table-cell-value tm-value icon-before icon-ton">{price}</div></div></td>
    <td><div class="table-cell"><div class="tm-datetime"><span class="wide-only"><time datetime="{when}">x</time></span></div></div></td>
  </tr>"""


USER = '<a href="https://t.me/alice" target="_blank" class="tm-inline-nowrap">@alice</a>'
NAME_ONLY = '<span class="tm-inline-nowrap accent-color">Bob &amp; Co†</span>'
STARS_CELL = "table-cell-value tm-value tm-nowrap"
HEADER = "<thead><tr><th>Recipient</th><th>Stars</th><th>Price</th><th>Date</th></tr></thead>"

STARS_HTML = HEADER + (
    row(USER, "1,500", '2<span class="mini-frac">.2822</span>', "2026-11-23T23:14:46+00:00", STARS_CELL)
    + row(NAME_ONLY, "50", '0<span class="mini-frac">.7506</span>', "2026-11-23T19:37:47+00:00", STARS_CELL)
    + row(USER, "100", "1", "2026-11-23T10:00:00+00:00", STARS_CELL)
)
PREMIUM_HTML = HEADER + (
    row(USER, "6 months", '16<span class="mini-frac">.2300</span>', "2026-11-22T21:07:47+00:00", "tm-nowrap")
    + row(USER, "1 year", '30<span class="mini-frac">.6500</span>', "2026-11-22T10:53:00+00:00", "tm-nowrap")
)


@pytest.mark.asyncio
async def test_get_stars_history_parses_rows(client: FragmentClient) -> None:
    with patch.object(client._transport, "fetch_page", AsyncMock(return_value=STARS_HTML)) as fetch:
        entries = await client.get_stars_history()

    fetch.assert_awaited_once_with(STARS_HISTORY_PAGE)
    assert entries[0] == StarsHistoryEntry(
        username="alice",
        name="@alice",
        stars=1500,
        gram=Decimal("2.2822"),
        date=datetime(2026, 11, 23, 23, 14, 46, tzinfo=UTC),
    )
    assert entries[2].gram == Decimal("1")


@pytest.mark.asyncio
async def test_get_stars_history_keeps_recipient_shown_by_name_only(client: FragmentClient) -> None:
    with patch.object(client._transport, "fetch_page", AsyncMock(return_value=STARS_HTML)):
        entries = await client.get_stars_history()

    assert len(entries) == 3
    assert (entries[1].username, entries[1].name) == (None, "Bob & Co†")


@pytest.mark.asyncio
async def test_get_stars_history_oldest_first_asks_for_ascending_order(client: FragmentClient) -> None:
    with patch.object(client._transport, "fetch_page", AsyncMock(return_value=STARS_HTML)) as fetch:
        await client.get_stars_history(newest_first=False)

    fetch.assert_awaited_once_with(f"{STARS_HISTORY_PAGE}?sort=asc")


@pytest.mark.asyncio
async def test_get_premium_history_reads_months_and_years(client: FragmentClient) -> None:
    with patch.object(client._transport, "fetch_page", AsyncMock(return_value=PREMIUM_HTML)) as fetch:
        entries = await client.get_premium_history()

    fetch.assert_awaited_once_with(PREMIUM_HISTORY_PAGE)
    assert all(isinstance(e, PremiumHistoryEntry) for e in entries)
    assert [e.months for e in entries] == [6, 12]
    assert entries[1].gram == Decimal("30.6500")


@pytest.mark.asyncio
async def test_get_history_empty_page(client: FragmentClient) -> None:
    with patch.object(client._transport, "fetch_page", AsyncMock(return_value="<html></html>")):
        assert await client.get_stars_history() == []
        assert await client.get_premium_history() == []


@pytest.mark.asyncio
async def test_get_premium_history_unknown_duration_is_a_parse_error(client: FragmentClient) -> None:
    html = row(USER, "forever", "1", "2026-11-22T21:07:47+00:00", "tm-nowrap")
    with patch.object(client._transport, "fetch_page", AsyncMock(return_value=html)), pytest.raises(ParseError):
        await client.get_premium_history()


@pytest.mark.asyncio
async def test_get_history_row_without_a_cell_is_a_parse_error_not_a_dropped_purchase(client: FragmentClient) -> None:
    html = "<tr><td>no cells Fragment would render</td></tr>"
    with patch.object(client._transport, "fetch_page", AsyncMock(return_value=html)), pytest.raises(ParseError):
        await client.get_stars_history()


@pytest.mark.asyncio
async def test_get_stars_history_unreadable_amount_is_a_parse_error(client: FragmentClient) -> None:
    html = row(USER, "lots", "1", "2026-11-22T21:07:47+00:00", STARS_CELL)
    with patch.object(client._transport, "fetch_page", AsyncMock(return_value=html)), pytest.raises(ParseError):
        await client.get_stars_history()
