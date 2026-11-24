"""search_usernames / search_numbers / search_gifts: how the arguments reach Fragment and how its answers are read."""

import json

import pytest

from pyfragment import ConfigurationError, FragmentAPIError, FragmentClient
from pyfragment.constants.fragment import FRAGMENT_BASE_URL, GIFTS_PAGE, NUMBERS_PAGE
from pyfragment.domains.marketplace.models import GiftsResult, NumbersResult, UsernamesResult
from pyfragment.enums import ApiMethod, AuctionFilter, AuctionSort, GiftView, MarketplaceType
from tests.support import fixtures
from tests.support.fake_fragment import FakeFragment

SEARCH = ApiMethod.SEARCH_AUCTIONS


class TestSearchUsernames:
    async def test_plain_search(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(SEARCH, {"html": fixtures.html("usernames_search.html")})

        result = await client.search_usernames("a")

        assert [item["name"] for item in result.items] == ["@aini", "@a_34", "@aban"]
        assert result.next_offset_id is None
        assert fragment.calls[0].data == {"type": MarketplaceType.USERNAMES, "query": "a"}
        assert fragment.calls[0].page_url == FRAGMENT_BASE_URL

    async def test_sort_filter_and_offset_are_sent(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(SEARCH, {"html": ""})

        await client.search_usernames("durov", sort=AuctionSort.PRICE_DESC, filter=AuctionFilter.AUCTION, offset_id="offset_10")

        assert fragment.calls[0].data == {
            "type": MarketplaceType.USERNAMES,
            "query": "durov",
            "sort": "price_desc",
            "filter": "auction",
            "offset_id": "offset_10",
        }

    async def test_enum_or_string_mean_the_same(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(SEARCH, {"html": ""})

        await client.search_usernames(sort=AuctionSort.ENDING, filter=AuctionFilter.SOLD)
        await client.search_usernames(sort="  Ending ", filter="SOLD")

        assert fragment.calls[0].data == fragment.calls[1].data

    async def test_the_default_filter_is_the_empty_string(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(SEARCH, {"html": ""})

        await client.search_usernames(filter="")

        assert fragment.calls[0].data["filter"] == ""

    @pytest.mark.parametrize("kwargs", [{"sort": "cheapest"}, {"filter": "free"}])
    async def test_invalid_sort_or_filter_fails_before_any_call(
        self, client: FragmentClient, fragment: FakeFragment, kwargs: dict[str, str]
    ) -> None:
        with pytest.raises(ConfigurationError, match="Supported values"):
            await client.search_usernames(**kwargs)  # type: ignore[arg-type]

        assert fragment.calls == []

    async def test_paginated_response_is_stitched_from_body_and_foot(
        self, client: FragmentClient, fragment: FakeFragment
    ) -> None:
        html = fixtures.html("usernames_listing.html")
        half = html.index('<tr class="tm-row-selectable">', html.index("tm-row-selectable") + 40)
        footer = '<a class="js-load-more" data-next-offset="500">Show more</a>'
        fragment.reply(SEARCH, {"part": True, "body": html[:half], "foot": html[half:] + footer})

        result = await client.search_usernames(offset_id="3")

        assert len(result.items) == 3
        assert result.next_offset_id == "500"

    async def test_api_error_is_raised(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(SEARCH, {"error": "Too many requests"})

        with pytest.raises(FragmentAPIError, match="Too many requests"):
            await client.search_usernames()


class TestSearchNumbers:
    async def test_numbers_listing(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(SEARCH, {"html": fixtures.html("numbers_listing.html")})

        result = await client.search_numbers("888", sort="listed", filter="sale", offset_id="7")

        assert [item["slug"] for item in result.items] == ["number/88802979151", "number/88801642359", "number/88801947637"]
        assert fragment.calls[0].data == {
            "type": MarketplaceType.NUMBERS,
            "query": "888",
            "sort": "listed",
            "filter": "sale",
            "offset_id": "7",
        }
        assert fragment.calls[0].page_url == NUMBERS_PAGE

    async def test_invalid_sort_fails_before_any_call(self, client: FragmentClient, fragment: FakeFragment) -> None:
        with pytest.raises(ConfigurationError):
            await client.search_numbers(sort="nope")

        assert fragment.calls == []

    async def test_api_error_is_raised(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(SEARCH, {"error": "Server error"})

        with pytest.raises(FragmentAPIError):
            await client.search_numbers()


class TestSearchGifts:
    async def test_grid_search_with_a_next_offset(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(SEARCH, {"html": fixtures.html("gifts_listing.html")})

        result = await client.search_gifts("shard")

        assert len(result.items) == 5
        assert result.next_offset == 60
        assert fragment.calls[0].data == {"type": MarketplaceType.GIFTS, "query": "shard"}
        assert fragment.calls[0].page_url == GIFTS_PAGE

    async def test_collection_view_and_offset_are_sent(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(SEARCH, {"html": ""})

        await client.search_gifts(
            collection="plushpepe", sort=AuctionSort.PRICE_ASC, filter="sold", view=GiftView.LIST, offset=60
        )

        assert fragment.calls[0].data == {
            "type": MarketplaceType.GIFTS,
            "query": "",
            "sort": "price_asc",
            "filter": "sold",
            "collection": "plushpepe",
            "view": "list",
            "offset_id": 60,
        }

    async def test_view_accepts_a_string_in_any_case(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(SEARCH, {"html": ""})

        await client.search_gifts(view="List")

        assert fragment.calls[0].data["view"] == "list"

    async def test_list_view_answer_is_parsed(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(SEARCH, {"html": fixtures.html("gifts_list.html")})

        result = await client.search_gifts(view="list")

        assert [item["name"] for item in result.items][0] == "Astral Shard #1445"
        assert result.next_offset == 60

    async def test_attribute_names_are_case_insensitive_and_sent_as_json_arrays(
        self, client: FragmentClient, fragment: FakeFragment
    ) -> None:
        fragment.reply(SEARCH, {"html": ""})

        await client.search_gifts(collection="plushpepe", attr={"model": ["Pepe", "Frog"], "BACKDROP": ["Black"], "Symbol": []})

        data = fragment.calls[0].data
        assert json.loads(data["attr[Model]"]) == ["Pepe", "Frog"]
        assert json.loads(data["attr[Backdrop]"]) == ["Black"]
        assert json.loads(data["attr[Symbol]"]) == []
        assert not [
            key for key in data if key.startswith("attr[") and key not in {"attr[Model]", "attr[Backdrop]", "attr[Symbol]"}
        ]

    @pytest.mark.parametrize(
        "kwargs",
        [{"view": "table"}, {"attr": {"Colour": ["red"]}}, {"sort": "nope"}, {"filter": "nope"}],
    )
    async def test_invalid_arguments_fail_before_any_call(
        self, client: FragmentClient, fragment: FakeFragment, kwargs: dict[str, object]
    ) -> None:
        with pytest.raises(ConfigurationError, match="Supported values"):
            await client.search_gifts(**kwargs)  # type: ignore[arg-type]

        assert fragment.calls == []

    async def test_paginated_response_is_stitched(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(SEARCH, fixtures.response("gifts_next_page.json"))

        result = await client.search_gifts("plush", offset=60)

        assert [item["name"] for item in result.items] == ["Plush Pepe #1274", "Plush Pepe #300", "Plush Pepe #404"]
        assert result.next_offset == 120

    async def test_api_error_is_raised(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(SEARCH, {"error": "Too many requests"})

        with pytest.raises(FragmentAPIError, match="Too many requests"):
            await client.search_gifts()


@pytest.mark.parametrize(
    ("result", "text"),
    [
        (UsernamesResult(items=[], next_offset_id="5"), "UsernamesResult(items=[], next_offset_id='5')"),
        (NumbersResult(items=[], next_offset_id=None), "NumbersResult(items=[], next_offset_id=None)"),
        (GiftsResult(items=[], next_offset=60), "GiftsResult(items=[], next_offset=60)"),
    ],
)
def test_results_have_a_readable_repr(result: object, text: str) -> None:
    assert repr(result) == text
