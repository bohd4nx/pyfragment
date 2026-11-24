"""Reading Fragment's marketplace listings (usernames, numbers, gifts) into items."""

import pytest

from pyfragment.domains.marketplace.parser import normalize_price, parse_auction_rows, parse_gift_items
from tests.support import fixtures


class TestUsernameRows:
    def test_one_row_per_status_with_price_and_date(self) -> None:
        items, next_offset = parse_auction_rows(fixtures.html("usernames_listing.html"))

        assert items == [
            {
                "slug": "username/john_pozer",
                "name": "@john_pozer",
                "status": None,
                "price": "6.00",
                "date": "2026-11-24T18:36:05+00:00",
            },
            {
                "slug": "username/bob_cwelowniczy",
                "name": "@bob_cwelowniczy",
                "status": "For sale",
                "price": "6.00",
                "date": "2026-11-30T20:42:32+00:00",
            },
            {
                "slug": "username/cumshe",
                "name": "@cumshe",
                "status": "Sold",
                "price": "0.10",
                "date": "2026-03-13T08:59:47+00:00",
            },
        ]
        assert next_offset is None

    def test_search_result_statuses_and_thousands_separators(self) -> None:
        items, _ = parse_auction_rows(fixtures.html("usernames_search.html"))

        assert [(item["name"], item["status"], item["price"], item["date"]) for item in items] == [
            ("@aini", "On auction", "17777.00", "2026-11-24T08:53:43+00:00"),
            ("@a_34", "Available", "5050.00", None),
            ("@aban", "Available", "5050.00", None),
        ]

    def test_the_footer_row_without_a_link_is_not_an_item(self) -> None:
        html = fixtures.html("usernames_search.html")

        assert "and over 5.38M more" in html
        items, next_offset = parse_auction_rows(html)

        assert len(items) == 3
        assert next_offset is None

    def test_next_offset_is_read_from_the_show_more_link(self) -> None:
        html = fixtures.html("usernames_listing.html") + '<a class="js-load-more" data-next-offset="500">Show more</a>'

        assert parse_auction_rows(html)[1] == "500"

    def test_nothing_to_parse(self) -> None:
        assert parse_auction_rows("") == ([], None)


class TestNumberRows:
    def test_numbers_keep_their_formatted_name(self) -> None:
        items, next_offset = parse_auction_rows(fixtures.html("numbers_listing.html"))

        assert [(item["slug"], item["name"], item["status"], item["price"]) for item in items] == [
            ("number/88802979151", "+888 0297 9151", None, "243.00"),
            ("number/88801642359", "+888 0164 2359", "For sale", "3440.00"),
            ("number/88801947637", "+888 0164 2359".replace("0164 2359", "0194 7637"), "Sold", "2.00"),
        ]
        assert [item["date"] for item in items] == [
            "2027-11-19T05:46:11+00:00",
            "2026-11-30T15:19:31+00:00",
            "2022-12-06T19:00:02+00:00",
        ]
        assert next_offset is None


class TestGiftItems:
    def test_grid_cards_cover_every_status(self) -> None:
        items, next_offset = parse_gift_items(fixtures.html("gifts_listing.html"))

        assert [(item["name"], item["status"], item["price"]) for item in items] == [
            ("Astral Shard #1445", "Not for sale", None),
            ("Snoop Dogg #440169", "On auction", "4.00"),
            ("Candy Cane #155403", "Available", "5.00"),
            ("Whip Cupcake #275414", "For sale", "6.00"),
            ("Desk Calendar #160157", "Sold", "0.10"),
        ]
        assert items[0]["slug"] == "gift/astralshard-1445"
        assert items[0]["date"] == "2025-02-21T16:50:51+00:00"
        assert items[2]["date"] is None
        assert next_offset == 60

    def test_next_page_response_stitches_body_and_foot(self) -> None:
        response = fixtures.response("gifts_next_page.json")

        items, next_offset = parse_gift_items(response["body"] + response["foot"])

        assert [item["name"] for item in items] == ["Plush Pepe #1274", "Plush Pepe #300", "Plush Pepe #404"]
        assert {item["status"] for item in items} == {"Sold"}
        assert items[0]["price"] == "8200.00"
        assert next_offset == 120

    def test_list_view_is_parsed_like_table_rows(self) -> None:
        items, next_offset = parse_gift_items(fixtures.html("gifts_list.html"))

        assert [(item["slug"], item["name"], item["status"], item["price"]) for item in items] == [
            ("gift/astralshard-1445", "Astral Shard #1445", "Not for sale", None),
            ("gift/snoopdogg-440169", "Snoop Dogg #440169", None, "4.00"),
            ("gift/whipcupcake-275414", "Whip Cupcake #275414", "For sale", "6.00"),
            ("gift/instantramen-235657", "Instant Ramen #235657", "For sale", "6.00"),
        ]
        assert next_offset == 60

    def test_cards_without_a_link_are_ignored(self) -> None:
        html = '<a class="tm-grid-item"><div class="item-name">Ghost</div></a>'

        assert parse_gift_items(html) == ([], None)


class TestNormalizePrice:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [("24,740", "24740.00"), ("6", "6.00"), ("0.1", "0.10"), ("1,234,567.5", "1234567.50"), (None, None), ("n/a", "n/a")],
    )
    def test_price(self, raw: str | None, expected: str | None) -> None:
        assert normalize_price(raw) == expected


class TestGiftCardWithoutStatus:
    def test_status_is_none(self) -> None:
        html = '<a href="/gift/ghost-1" class="tm-grid-item"><div class="item-name">Ghost</div></a>'

        assert parse_gift_items(html)[0] == [
            {"slug": "gift/ghost-1", "name": "Ghost", "status": None, "price": None, "date": None}
        ]
