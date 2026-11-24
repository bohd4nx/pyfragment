"""get_my_usernames / numbers / gifts: paging through the account's ``getAssetsList``."""

import re
from typing import Any

import pytest

from pyfragment import FragmentAPIError, FragmentClient
from pyfragment.constants.fragment import MY_ASSETS_PAGE
from pyfragment.enums import ApiMethod, AssetType
from tests.support import fixtures
from tests.support.fake_fragment import FakeFragment

LIST = ApiMethod.GET_ASSETS_LIST


# The capture account owns nothing, so the shape of a real non-empty item is unknown: the items below are
# ``{"html": <one row>}``, with rows taken from the marketplace listings (the same markup the parsers read).
def table_rows(name: str) -> list[str]:
    return [row for row in re.findall(r"<tr\b.*?</tr>", fixtures.html(name), re.DOTALL) if 'href="/' in row]


def grid_cards(name: str) -> list[str]:
    return re.findall(r'<a\b[^>]*class="tm-grid-item".*?</a>', fixtures.html(name), re.DOTALL)


def items(*rows: str) -> list[dict[str, str]]:
    return [{"html": row} for row in rows]


def page(rows: list[str], next_offset_id: Any = False) -> dict[str, Any]:
    return {"ok": True, "items": items(*rows), "next_offset_id": next_offset_id}


class TestEmptyAccount:
    async def test_nothing_owned(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(LIST, fixtures.response("assets_list_empty.json"))

        assert (await client.get_my_usernames()).items == []
        assert (await client.get_my_numbers()).items == []
        assert (await client.get_my_gifts()).items == []

    async def test_one_request_per_kind_with_the_asset_type(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(LIST, fixtures.response("assets_list_empty.json"))

        await client.get_my_usernames()
        await client.get_my_numbers()
        await client.get_my_gifts()

        assert [call.data for call in fragment.calls] == [
            {"type": AssetType.USERNAMES, "offset_id": 0},
            {"type": AssetType.NUMBERS, "offset_id": 0},
            {"type": AssetType.GIFTS, "offset_id": 0},
        ]
        assert {call.page_url for call in fragment.calls} == {MY_ASSETS_PAGE}


class TestOwnedItems:
    async def test_usernames(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(LIST, page(table_rows("usernames_listing.html")))

        result = await client.get_my_usernames()

        assert [(item["name"], item["status"], item["price"]) for item in result.items] == [
            ("@john_pozer", None, "6.00"),
            ("@bob_cwelowniczy", "For sale", "6.00"),
            ("@cumshe", "Sold", "0.10"),
        ]
        assert len(fragment.calls) == 1

    async def test_numbers(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(LIST, page(table_rows("numbers_listing.html")))

        result = await client.get_my_numbers()

        assert [item["slug"] for item in result.items] == ["number/88802979151", "number/88801642359", "number/88801947637"]

    async def test_gifts_in_the_grid_markup(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(LIST, page(grid_cards("gifts_listing.html")))

        result = await client.get_my_gifts()

        assert [item["name"] for item in result.items][:2] == ["Astral Shard #1445", "Snoop Dogg #440169"]
        assert len(result.items) == 5

    async def test_gifts_in_the_table_markup(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(LIST, page(table_rows("gifts_list.html")))

        result = await client.get_my_gifts()

        assert [item["slug"] for item in result.items][0] == "gift/astralshard-1445"
        assert len(result.items) == 4

    async def test_an_item_without_html_adds_nothing(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(LIST, {"items": [{}, *items(*table_rows("usernames_listing.html")[:1])], "next_offset_id": False})

        assert len((await client.get_my_usernames()).items) == 1


class TestPaging:
    async def test_pages_are_followed_until_there_is_no_next_offset(
        self, client: FragmentClient, fragment: FakeFragment
    ) -> None:
        rows = table_rows("usernames_listing.html")
        fragment.reply(LIST, page(rows[:1], "2"), page(rows[1:2], "3"), page(rows[2:], False))

        result = await client.get_my_usernames()

        assert [item["name"] for item in result.items] == ["@john_pozer", "@bob_cwelowniczy", "@cumshe"]
        assert [call.data["offset_id"] for call in fragment.sent(LIST)] == [0, "2", "3"]

    async def test_stops_when_the_next_offset_repeats(self, client: FragmentClient, fragment: FakeFragment) -> None:
        rows = table_rows("usernames_listing.html")
        fragment.reply(LIST, page(rows[:1], "2"), page(rows[1:], "2"))

        result = await client.get_my_usernames()

        assert len(result.items) == 3
        assert [call.data["offset_id"] for call in fragment.sent(LIST)] == [0, "2"]

    @pytest.mark.parametrize("last", [False, None, "", 0])
    async def test_a_falsy_next_offset_ends_the_listing(
        self, client: FragmentClient, fragment: FakeFragment, last: object
    ) -> None:
        fragment.reply(LIST, page(table_rows("numbers_listing.html"), last))

        await client.get_my_numbers()

        assert len(fragment.sent(LIST)) == 1


class TestErrors:
    async def test_error_response_raises(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(LIST, {"error": "Access denied"})

        with pytest.raises(FragmentAPIError, match="Access denied"):
            await client.get_my_usernames()

    async def test_error_on_a_later_page_raises_instead_of_returning_a_partial_list(
        self, client: FragmentClient, fragment: FakeFragment
    ) -> None:
        fragment.reply(LIST, page(table_rows("usernames_listing.html")[:1], "2"), {"error": "Too many requests"})

        with pytest.raises(FragmentAPIError, match="Too many requests"):
            await client.get_my_usernames()
