"""Parse real fragment.com listing markup (trimmed fixtures) and check every extracted field."""

from unittest.mock import AsyncMock, patch

import pytest

from pyfragment import AuctionItem, FragmentClient
from pyfragment.domains.marketplace.parser import parse_auction_rows, parse_gift_items
from tests.shared import fixture_html, fixture_json

# (slug, name, status, price, date)
Row = tuple[str, str, str | None, str | None, str | None]


def _rows(items: list[AuctionItem]) -> list[Row]:
    return [(i["slug"], i["name"], i["status"], i["price"], i["date"]) for i in items]


# Usernames and numbers


def test_parse_usernames_one_row_per_status() -> None:
    items, next_offset_id = parse_auction_rows(fixture_html("usernames_one_per_status.html"))

    assert next_offset_id is None
    assert _rows(items) == [
        ("username/notcoin_e", "@notcoin_e", "Available", "5000.00", None),
        ("username/adriankhalif", "@adriankhalif", "For sale", "6.00", "2026-10-04T20:44:54+00:00"),
        ("username/durovbro", "@durovbro", "On auction", "11.00", "2026-09-28T13:22:02+00:00"),
        ("username/danbao", "@danbao", "Sold", "1583948.00", "2026-02-07T17:04:13+00:00"),
        ("username/durov", "@durov", "Taken", None, None),
        # A plain auction row carries no status label, only a countdown.
        ("username/board", "@board", None, "24740.00", "2026-09-28T10:41:30+00:00"),
    ]


def test_parse_usernames_search_skips_show_more_footer_and_reports_offset() -> None:
    items, next_offset_id = parse_auction_rows(fixture_html("usernames_search_result.html"))

    assert [i["name"] for i in items] == ["@durov", "@durovbro", "@durovsay", "@durovcap", "@durov69"]
    assert next_offset_id == "500"


def test_parse_taken_username_has_no_price_even_though_the_cell_says_unknown() -> None:
    items, _ = parse_auction_rows(fixture_html("usernames_search_result.html"))

    assert (items[0]["status"], items[0]["price"], items[0]["date"]) == ("Taken", None, None)


def test_parse_numbers_one_row_per_status() -> None:
    items, next_offset_id = parse_auction_rows(fixture_html("numbers_one_per_status.html"))

    assert next_offset_id is None
    assert _rows(items) == [
        ("number/88807303695", "+888 0730 3695", "For sale", "2370.00", "2026-10-04T23:08:37+00:00"),
        ("number/8888666", "+888 8 666", "Sold", "666666.00", "2026-08-25T10:17:44+00:00"),
        ("number/88800001312", "+888 0000 1312", None, "25560.00", "2027-03-30T15:42:56+00:00"),
    ]


def test_parse_numbers_search() -> None:
    items, next_offset_id = parse_auction_rows(fixture_html("numbers_search_result.html"))

    assert _rows(items) == [
        ("number/88809888888", "+888 0988 8888", "For sale", "888888888.00", "2027-08-02T10:41:11+00:00"),
        ("number/88808888880", "+888 0888 8880", "For sale", "688000.00", "2027-08-27T22:23:32+00:00"),
    ]
    assert next_offset_id == "500"


def test_parse_auction_rows_empty_html() -> None:
    assert parse_auction_rows("") == ([], None)


# Gifts


def test_parse_gifts_one_card_per_status() -> None:
    items, next_offset = parse_gift_items(fixture_html("gifts_one_per_status.html"))

    assert next_offset == 60
    assert _rows(items) == [
        ("gift/jollychimp-102451", "Jolly Chimp #102451", "Available", "15.00", None),
        ("gift/berrybox-421", "Berry Box #421", "For sale", "15.00", "2026-09-06T07:42:33+00:00"),
        ("gift/lunarsnake-38718", "Lunar Snake #38718", "Not for sale", None, "2026-09-27T22:40:31+00:00"),
        # The status of a gift on auction is split into a short and a full <span>; the full one wins.
        ("gift/libertyfigure-100", "Liberty Figure #100", "On auction", "256.00", "2027-08-28T00:56:36+00:00"),
        ("gift/plushpepe-1821", "Plush Pepe #1821", "Sold", "88888.00", "2026-02-05T14:41:27+00:00"),
    ]


def test_parse_gifts_drops_the_link_query_string_from_the_slug() -> None:
    items, _ = parse_gift_items(fixture_html("gifts_one_per_status.html"))

    assert all("?" not in i["slug"] for i in items)


def test_parse_gifts_empty_html() -> None:
    assert parse_gift_items("") == ([], None)


@pytest.mark.asyncio
async def test_search_gifts_paginated_response(client: FragmentClient) -> None:
    page = fixture_json("gifts_next_page_response.json")

    with patch.object(client, "call", AsyncMock(return_value=page)):
        result = await client.search_gifts(offset=60)

    assert [i["name"] for i in result.items] == ["Scared Cat #17302", "Plush Pepe #1485", "Plush Pepe #1213"]
    assert result.next_offset == 120
