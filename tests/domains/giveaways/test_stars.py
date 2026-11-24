"""Running a Stars giveaway for a channel."""

import re
from typing import Any
from unittest.mock import AsyncMock

import pytest

from pyfragment import (
    AboveMaximumError,
    ChannelNotFoundError,
    ConfigurationError,
    FragmentAPIError,
    FragmentClient,
    InvalidPackageError,
    StarsGiveawayResult,
    VerificationError,
)
from pyfragment.constants.fragment import STARS_GIVEAWAY_PAGE
from pyfragment.constants.limits import STARS_GIVEAWAY, STARS_GIVEAWAY_MIN_PER_WINNER, STARS_WINNERS
from pyfragment.domains.giveaways.stars import STARS_GIVEAWAY_FLOW
from pyfragment.enums import ApiMethod, PaymentMethod
from tests.domains.purchase_script import CONFIRM_METHOD, script_purchase
from tests.support import fixtures
from tests.support.data import COMMENT, RECIPIENT_TOKEN, REQ_ID, TX_BOC, TX_HASH
from tests.support.fake_fragment import FakeFragment

FOUND = (ApiMethod.SEARCH_STARS_GIVEAWAY_RECIPIENT, fixtures.response("stars_recipient_found.json"))
STATE = ApiMethod.UPDATE_STARS_GIVEAWAY_STATE
PRICES = ApiMethod.UPDATE_STARS_GIVEAWAY_PRICES


def script(fragment: FakeFragment, confirmed: bool = True, replies: dict[str, Any] | None = None) -> None:
    script_purchase(fragment, STARS_GIVEAWAY_FLOW, FOUND, confirmed, {PRICES: {"ok": True}, **(replies or {})})


class TestGiveawayStars:
    async def test_whole_flow_in_fragments_order(self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock) -> None:
        script(fragment)

        result = await client.giveaway_stars("example", winners=3, amount=1000)

        assert fragment.methods == [
            ApiMethod.SEARCH_STARS_GIVEAWAY_RECIPIENT,
            STATE,
            PRICES,
            ApiMethod.INIT_GIVEAWAY_STARS_REQUEST,
            ApiMethod.GET_GIVEAWAY_STARS_LINK,
            CONFIRM_METHOD,
            STATE,
        ]
        assert {call.page_url for call in fragment.calls} == {STARS_GIVEAWAY_PAGE}
        assert result == StarsGiveawayResult(
            transaction_id=TX_HASH, confirmed=True, comment=COMMENT, boc=TX_BOC, channel="example", winners=3, amount=1000
        )

    async def test_request_payloads(self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock) -> None:
        script(fragment)

        await client.giveaway_stars("example", winners=3, amount=1000)

        assert fragment.calls[0].data == {"query": "example"}
        assert fragment.sent(PRICES)[0].data == {"quantity": 3, "stars": 1000}
        assert fragment.sent(ApiMethod.INIT_GIVEAWAY_STARS_REQUEST)[0].data == {
            "recipient": RECIPIENT_TOKEN,
            "quantity": "3",
            "stars": "1000",
            "payment_method": PaymentMethod.GRAM,
        }
        assert fragment.sent(ApiMethod.GET_GIVEAWAY_STARS_LINK)[0].data == {"transaction": 1, "id": REQ_ID}

    async def test_usdt_payment_reaches_the_invoice_and_the_transfer(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock
    ) -> None:
        script(fragment)

        await client.giveaway_stars("example", 3, 1000, payment_method=PaymentMethod.USDT_GRAM)

        assert fragment.sent(ApiMethod.INIT_GIVEAWAY_STARS_REQUEST)[0].data["payment_method"] == PaymentMethod.USDT_GRAM
        assert paid.await_args is not None
        assert paid.await_args.kwargs == {"payment_method": PaymentMethod.USDT_GRAM, "req_id": REQ_ID}

    async def test_unconfirmed_when_fragment_never_reports_done(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock
    ) -> None:
        script(fragment, confirmed=False)
        client.confirm_timeout = 0.02

        result = await client.giveaway_stars("example", 3, 1000)

        assert result.confirmed is False
        assert result.transaction_id == TX_HASH

    @pytest.mark.parametrize("winners", [STARS_WINNERS.min - 1, STARS_WINNERS.max + 1, 1.5, True])
    async def test_winners_out_of_range_are_rejected_before_any_call(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock, winners: Any
    ) -> None:
        with pytest.raises(ConfigurationError, match=STARS_WINNERS.label):
            await client.giveaway_stars("example", winners, STARS_GIVEAWAY.min)

        assert fragment.calls == []

    @pytest.mark.parametrize("amount", [STARS_GIVEAWAY.min - 1, STARS_GIVEAWAY.max + 1, 500.5, True])
    async def test_package_out_of_range_is_rejected_before_any_call(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock, amount: Any
    ) -> None:
        with pytest.raises(ConfigurationError, match=STARS_GIVEAWAY.label):
            await client.giveaway_stars("example", 1, amount)

        assert fragment.calls == []

    @pytest.mark.parametrize(("winners", "amount"), [(6, 500), (11, 1_000), (101, 10_000)])
    async def test_more_winners_than_the_package_can_share_are_rejected_before_any_call(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock, winners: int, amount: int
    ) -> None:
        expected = ConfigurationError.TOO_MANY_WINNERS.format(
            amount=amount, max=amount // STARS_GIVEAWAY_MIN_PER_WINNER, per_winner=STARS_GIVEAWAY_MIN_PER_WINNER
        )

        with pytest.raises(ConfigurationError, match=re.escape(expected)):
            await client.giveaway_stars("example", winners, amount)

        assert fragment.calls == []

    @pytest.mark.parametrize(("winners", "amount"), [(5, 500), (10, 1_000), (10_000, 1_000_000)])
    async def test_the_most_a_package_allows_goes_through(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock, winners: int, amount: int
    ) -> None:
        script(fragment)

        result = await client.giveaway_stars("example", winners, amount)

        assert (result.winners, result.amount) == (winners, amount)

    @pytest.mark.parametrize("payment_method", ["btc", "usdt_eth", "usdt_pol"])
    async def test_payment_method_it_cannot_sign_for_is_rejected_before_any_call(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock, payment_method: Any
    ) -> None:
        with pytest.raises(ConfigurationError, match="Invalid payment method"):
            await client.giveaway_stars("example", 1, 500, payment_method=payment_method)

        assert fragment.calls == []

    @pytest.mark.parametrize("query", ["@example", "example", "https://t.me/id2757542991"])
    async def test_channel_is_searched_as_given(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock, query: str
    ) -> None:
        script(fragment)

        result = await client.giveaway_stars(query, 1, 500)

        assert fragment.calls[0].data == {"query": query}
        assert result.channel == query

    @pytest.mark.parametrize("fixture", ["giveaway_channel_not_found.json", "giveaway_not_a_channel.json"])
    async def test_not_a_channel_stops_before_the_page_opens(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock, fixture: str
    ) -> None:
        fragment.reply(ApiMethod.SEARCH_STARS_GIVEAWAY_RECIPIENT, fixtures.response(fixture))

        with pytest.raises(ChannelNotFoundError, match="example"):
            await client.giveaway_stars("example", 1, 500)

        assert fragment.methods == [ApiMethod.SEARCH_STARS_GIVEAWAY_RECIPIENT]

    @pytest.mark.parametrize(
        ("fixture", "error"),
        [("giveaway_too_many_winners.json", AboveMaximumError), ("giveaway_bad_package.json", InvalidPackageError)],
    )
    async def test_package_fragment_refuses_is_raised_from_the_price_check(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock, fixture: str, error: type[Exception]
    ) -> None:
        script(fragment, replies={PRICES: fixtures.response(fixture)})

        with pytest.raises(error):
            await client.giveaway_stars("example", 3, 1000)

        assert ApiMethod.INIT_GIVEAWAY_STARS_REQUEST not in fragment.methods
        paid.assert_not_awaited()

    async def test_too_many_winners_error_carries_the_maximum(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock
    ) -> None:
        script(fragment, replies={PRICES: fixtures.response("giveaway_too_many_winners.json")})

        with pytest.raises(AboveMaximumError) as exc_info:
            await client.giveaway_stars("example", 3, 1000)

        assert exc_info.value.maximum == 5

    async def test_invoice_reply_without_request_id_is_not_paid(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock
    ) -> None:
        script(fragment, replies={ApiMethod.INIT_GIVEAWAY_STARS_REQUEST: {"amount": "0.1"}})

        with pytest.raises(FragmentAPIError):
            await client.giveaway_stars("example", 3, 1000)

        paid.assert_not_awaited()

    async def test_verification_required(self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock) -> None:
        script(fragment, replies={ApiMethod.GET_GIVEAWAY_STARS_LINK: {"need_verify": True}})

        with pytest.raises(VerificationError):
            await client.giveaway_stars("example", 3, 1000)

        paid.assert_not_awaited()


class TestStarsGiveawayResultRepr:
    def test_shows_the_package_and_its_winners(self) -> None:
        result = StarsGiveawayResult(
            transaction_id=TX_HASH, confirmed=True, comment=COMMENT, boc=TX_BOC, channel="example", winners=3, amount=1000
        )

        assert repr(result) == (
            f"StarsGiveawayResult(channel='example', winners=3, amount=1000 stars, tx='{TX_HASH}', confirmed=True)"
        )
