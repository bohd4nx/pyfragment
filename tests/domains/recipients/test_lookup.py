"""Finding the Telegram user or channel a purchase goes to."""

import pytest

from pyfragment import (
    AlreadySubscribedError,
    ChannelNotFoundError,
    FragmentAPIError,
    FragmentClient,
    Recipient,
    UserNotFoundError,
)
from pyfragment.constants.fragment import STARS_PAGE
from pyfragment.domains.giveaways.stars import STARS_GIVEAWAY_FLOW
from pyfragment.domains.purchases.premium import PREMIUM_FLOW
from pyfragment.domains.purchases.stars import STARS_FLOW
from pyfragment.domains.recipients import find_channel, find_user
from pyfragment.enums import ApiMethod
from tests.support import fixtures
from tests.support.data import RECIPIENT_TOKEN
from tests.support.fake_fragment import FakeFragment

SEARCH_USER = (STARS_FLOW, {"query": "example", "quantity": ""})
SEARCH_CHANNEL = (STARS_GIVEAWAY_FLOW, {"query": "example"})


class TestFindUser:
    async def test_found_recipient_carries_what_fragment_returned(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(ApiMethod.SEARCH_STARS_RECIPIENT, fixtures.response("stars_recipient_found.json"))

        recipient = await find_user(client, *SEARCH_USER, "example")

        assert recipient == Recipient(
            recipient=RECIPIENT_TOKEN, username="example", name="Example", photo=recipient.photo, myself=False
        )
        assert recipient.photo and recipient.photo.startswith("<img")
        assert fragment.calls[0].data == {"query": "example", "quantity": ""}
        assert fragment.calls[0].page_url == STARS_PAGE

    async def test_unknown_username_is_user_not_found(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(ApiMethod.SEARCH_STARS_RECIPIENT, fixtures.response("stars_recipient_not_found.json"))

        with pytest.raises(UserNotFoundError, match="example"):
            await find_user(client, *SEARCH_USER, "example")

    async def test_bot_or_channel_username_is_user_not_found(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(ApiMethod.SEARCH_STARS_RECIPIENT, fixtures.response("stars_recipient_not_a_user.json"))

        with pytest.raises(UserNotFoundError, match="example"):
            await find_user(client, *SEARCH_USER, "example")

    async def test_recipient_who_already_has_premium(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(ApiMethod.SEARCH_PREMIUM_GIFT_RECIPIENT, fixtures.response("premium_recipient_already_subscribed.json"))

        with pytest.raises(AlreadySubscribedError):
            await find_user(client, PREMIUM_FLOW, {"query": "example", "months": 3}, "example")

    async def test_other_errors_do_not_pose_as_a_missing_user(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(ApiMethod.SEARCH_STARS_RECIPIENT, {"error": "Too many requests"})

        with pytest.raises(FragmentAPIError, match="Too many requests") as caught:
            await find_user(client, *SEARCH_USER, "example")

        assert not isinstance(caught.value, UserNotFoundError)


class TestFindChannel:
    async def test_found_channel(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(ApiMethod.SEARCH_STARS_GIVEAWAY_RECIPIENT, fixtures.response("stars_recipient_found.json"))

        recipient = await find_channel(client, *SEARCH_CHANNEL, "example")

        assert recipient.recipient == RECIPIENT_TOKEN
        assert recipient.username == "example"

    async def test_unknown_channel(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(ApiMethod.SEARCH_STARS_GIVEAWAY_RECIPIENT, fixtures.response("giveaway_channel_not_found.json"))

        with pytest.raises(ChannelNotFoundError, match="example"):
            await find_channel(client, *SEARCH_CHANNEL, "example")

    async def test_user_or_bot_instead_of_a_channel(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(ApiMethod.SEARCH_STARS_GIVEAWAY_RECIPIENT, fixtures.response("giveaway_not_a_channel.json"))

        with pytest.raises(ChannelNotFoundError):
            await find_channel(client, *SEARCH_CHANNEL, "example")
