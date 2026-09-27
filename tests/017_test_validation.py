"""Check input validation (amounts, counts, giveaway limits, sort/filter) and error normalization."""

from unittest.mock import AsyncMock, patch

import pytest

from pyfragment import (
    AlreadySubscribedError,
    ChannelNotFoundError,
    ConfigurationError,
    FragmentAPIError,
    FragmentClient,
    UnexpectedError,
    UserNotFoundError,
)
from pyfragment.core.constants import STARS_WINNERS_MAX
from pyfragment.core.validation import is_int_in_range
from pyfragment.enums import AuctionFilter, AuctionSort, GiftAttribute, MarketplaceType

# is_int_in_range


@pytest.mark.parametrize(
    ("value", "expected"), [(1, True), (5, True), (0, False), (6, False), (True, False), (2.0, False), ("3", False)]
)
def test_is_int_in_range(value: object, expected: bool) -> None:
    assert is_int_in_range(value, 1, 5) is expected


# bool must not slip through as 1


@pytest.mark.asyncio
async def test_topup_gram_rejects_bool(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.topup_gram("@user", True)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_recharge_ads_rejects_bool(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.recharge_ads("@channel", True)  # type: ignore[arg-type]


# Stars giveaway: Fragment allows 1-5 winners


@pytest.mark.asyncio
@pytest.mark.parametrize("winners", [0, STARS_WINNERS_MAX + 1, 15, True])
async def test_giveaway_stars_rejects_invalid_winners(client: FragmentClient, winners: int) -> None:
    with pytest.raises(ConfigurationError, match="winners"):
        await client.giveaway_stars("@channel", winners, 500)


@pytest.mark.asyncio
@pytest.mark.parametrize("amount", [499, 1_000_001, True])
async def test_giveaway_stars_rejects_invalid_amount(client: FragmentClient, amount: int) -> None:
    with pytest.raises(ConfigurationError, match="Stars per winner"):
        await client.giveaway_stars("@channel", 1, amount)


@pytest.mark.asyncio
@pytest.mark.parametrize("winners", [0, 24_001, True])
async def test_giveaway_premium_rejects_invalid_winners(client: FragmentClient, winners: int) -> None:
    with pytest.raises(ConfigurationError, match="winners"):
        await client.giveaway_premium("@channel", winners)


# Marketplace sort/filter: Fragment silently ignores unknown values, so we validate them up front


@pytest.mark.asyncio
@pytest.mark.parametrize("search", ["search_usernames", "search_numbers", "search_gifts"])
async def test_search_rejects_unknown_sort(client: FragmentClient, search: str) -> None:
    with pytest.raises(ConfigurationError, match="Invalid sort order"):
        await getattr(client, search)(sort="cheapest")


@pytest.mark.asyncio
@pytest.mark.parametrize("search", ["search_usernames", "search_numbers", "search_gifts"])
async def test_search_rejects_unknown_filter(client: FragmentClient, search: str) -> None:
    with pytest.raises(ConfigurationError, match="Invalid filter"):
        await getattr(client, search)(filter="cheap")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("sort", "filter", "sent_sort", "sent_filter"),
    [
        (AuctionSort.PRICE_ASC, AuctionFilter.SOLD, "price_asc", "sold"),
        ("Price_Desc", "SALE", "price_desc", "sale"),
        (None, "", None, ""),
    ],
)
async def test_search_sends_normalized_sort_and_filter(
    client: FragmentClient, sort: str | None, filter: str, sent_sort: str | None, sent_filter: str
) -> None:
    call_mock = AsyncMock(return_value={"html": ""})
    with patch.object(client, "call", call_mock):
        await client.search_usernames("ton", sort=sort, filter=filter)

    sent = call_mock.await_args.args[1]
    assert sent.get("sort") == sent_sort
    assert sent["filter"] == sent_filter
    assert sent["type"] == MarketplaceType.USERNAMES


@pytest.mark.asyncio
async def test_giveaway_channel_not_found_raises_channel_error(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(return_value={"found": {}})):
        with pytest.raises(ChannelNotFoundError, match="channel") as exc_info:
            await client.giveaway_stars("@nochannel", 1, 500)

    assert isinstance(exc_info.value, UserNotFoundError)


@pytest.mark.asyncio
async def test_unexpected_errors_are_wrapped(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(side_effect=RuntimeError("boom"))):
        with pytest.raises(UnexpectedError, match="boom"):
            await client.search_usernames("ton")


# Gift traits: Fragment silently ignores unknown or wrongly cased attribute names


@pytest.mark.asyncio
async def test_search_gifts_rejects_unknown_attribute(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError, match="Invalid gift attribute 'rarity'"):
        await client.search_gifts(attr={"rarity": ["rare"]})


@pytest.mark.asyncio
async def test_search_gifts_sends_canonical_attribute_names(client: FragmentClient) -> None:
    call_mock = AsyncMock(return_value={"html": ""})
    with patch.object(client, "call", call_mock):
        await client.search_gifts(
            collection="bowtie", attr={"model": ["Bordeaux"], GiftAttribute.BACKDROP: ["Onyx Black", "Mint Green"]}
        )

    sent = call_mock.await_args.args[1]
    assert sent["attr[Model]"] == '["Bordeaux"]'
    assert sent["attr[Backdrop]"] == '["Onyx Black", "Mint Green"]'
    assert sent["collection"] == "bowtie"
    assert not any(key.lower() == "attr[model]" and key != "attr[Model]" for key in sent)


# Recipient search: real Fragment error texts map to specific exceptions, unknown errors surface as-is


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("search", "error", "exception"),
    [
        ("purchase_stars", "No Telegram users found.", UserNotFoundError),
        ("purchase_stars", "Please enter a username assigned to a user.", UserNotFoundError),
        ("purchase_premium", "This account is already subscribed to Telegram Premium.", AlreadySubscribedError),
        ("giveaway_stars", "No Telegram channels found.", ChannelNotFoundError),
        ("topup_gram", "No Telegram users found.", UserNotFoundError),
    ],
)
async def test_recipient_search_errors_map_to_exceptions(
    client: FragmentClient, search: str, error: str, exception: type[Exception]
) -> None:
    args = {"purchase_stars": (500,), "purchase_premium": (3,), "giveaway_stars": (1, 500), "topup_gram": (5,)}[search]
    with patch.object(client, "call", AsyncMock(return_value={"error": error})):
        with pytest.raises(exception):
            await getattr(client, search)("@target", *args)


@pytest.mark.asyncio
async def test_recipient_search_surfaces_unrelated_errors(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(return_value={"error": "Access denied"})):
        with pytest.raises(FragmentAPIError, match="Access denied") as exc_info:
            await client.purchase_stars("@target", 500)

    assert not isinstance(exc_info.value, UserNotFoundError)
