"""Running a Premium giveaway for a channel."""

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
    PremiumGiveawayResult,
    VerificationError,
)
from pyfragment.constants.fragment import PREMIUM_GIVEAWAY_PAGE
from pyfragment.constants.limits import PREMIUM_WINNERS
from pyfragment.domains.giveaways.premium import PREMIUM_GIVEAWAY_FLOW
from pyfragment.enums import ApiMethod, PaymentMethod
from tests.domains.purchase_script import CONFIRM_METHOD, script_purchase
from tests.support import fixtures
from tests.support.data import COMMENT, RECIPIENT_TOKEN, REQ_ID, TX_BOC, TX_HASH
from tests.support.fake_fragment import FakeFragment

FOUND = (ApiMethod.SEARCH_PREMIUM_GIVEAWAY_RECIPIENT, fixtures.response("stars_recipient_found.json"))
STATE = ApiMethod.UPDATE_PREMIUM_GIVEAWAY_STATE
PRICES = ApiMethod.UPDATE_PREMIUM_GIVEAWAY_PRICES


def script(fragment: FakeFragment, confirmed: bool = True, replies: dict[str, Any] | None = None) -> None:
    script_purchase(fragment, PREMIUM_GIVEAWAY_FLOW, FOUND, confirmed, {PRICES: {"ok": True}, **(replies or {})})


class TestGiveawayPremium:
    async def test_whole_flow_in_fragments_order(self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock) -> None:
        script(fragment)

        result = await client.giveaway_premium("example", winners=10, months=6)

        assert fragment.methods == [
            ApiMethod.SEARCH_PREMIUM_GIVEAWAY_RECIPIENT,
            STATE,
            PRICES,
            ApiMethod.INIT_GIVEAWAY_PREMIUM_REQUEST,
            ApiMethod.GET_GIVEAWAY_PREMIUM_LINK,
            CONFIRM_METHOD,
            STATE,
        ]
        assert {call.page_url for call in fragment.calls} == {PREMIUM_GIVEAWAY_PAGE}
        assert result == PremiumGiveawayResult(
            transaction_id=TX_HASH, confirmed=True, comment=COMMENT, boc=TX_BOC, channel="example", winners=10, amount=6
        )

    async def test_request_payloads(self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock) -> None:
        script(fragment)

        await client.giveaway_premium("example", winners=10, months=12)

        assert fragment.calls[0].data == {"query": "example", "quantity": 10, "months": 12}
        assert fragment.sent(STATE)[0].data["quantity"] == ""
        assert fragment.sent(PRICES)[0].data == {"quantity": 10}
        assert fragment.sent(ApiMethod.INIT_GIVEAWAY_PREMIUM_REQUEST)[0].data == {
            "recipient": RECIPIENT_TOKEN,
            "quantity": "10",
            "months": "12",
            "payment_method": PaymentMethod.GRAM,
        }
        assert fragment.sent(ApiMethod.GET_GIVEAWAY_PREMIUM_LINK)[0].data == {"transaction": 1, "id": REQ_ID}

    async def test_months_default_to_three(self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock) -> None:
        script(fragment)

        result = await client.giveaway_premium("example", 10)

        assert result.amount == 3
        assert fragment.calls[0].data["months"] == 3

    async def test_usdt_payment_reaches_the_invoice_and_the_transfer(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock
    ) -> None:
        script(fragment)

        await client.giveaway_premium("example", 10, 6, payment_method=PaymentMethod.USDT_GRAM)

        assert fragment.sent(ApiMethod.INIT_GIVEAWAY_PREMIUM_REQUEST)[0].data["payment_method"] == PaymentMethod.USDT_GRAM
        assert paid.await_args is not None
        assert paid.await_args.kwargs == {"payment_method": PaymentMethod.USDT_GRAM, "req_id": REQ_ID}

    async def test_unconfirmed_when_fragment_never_reports_done(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock
    ) -> None:
        script(fragment, confirmed=False)
        client.confirm_timeout = 0.02

        result = await client.giveaway_premium("example", 10)

        assert result.confirmed is False
        assert result.transaction_id == TX_HASH

    @pytest.mark.parametrize("winners", [PREMIUM_WINNERS.min - 1, PREMIUM_WINNERS.max + 1, 1.5, True])
    async def test_winners_out_of_range_are_rejected_before_any_call(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock, winners: Any
    ) -> None:
        with pytest.raises(ConfigurationError, match=PREMIUM_WINNERS.label):
            await client.giveaway_premium("example", winners)

        assert fragment.calls == []

    @pytest.mark.parametrize("months", [0, 4, 24, True])
    async def test_unsupported_duration_is_rejected_before_any_call(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock, months: Any
    ) -> None:
        with pytest.raises(ConfigurationError, match=re.escape(ConfigurationError.INVALID_MONTHS)):
            await client.giveaway_premium("example", 10, months)

        assert fragment.calls == []

    @pytest.mark.parametrize("payment_method", ["btc", "usdt_pol"])
    async def test_payment_method_it_cannot_sign_for_is_rejected_before_any_call(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock, payment_method: Any
    ) -> None:
        with pytest.raises(ConfigurationError, match="Invalid payment method"):
            await client.giveaway_premium("example", 10, payment_method=payment_method)

        assert fragment.calls == []

    @pytest.mark.parametrize("query", ["@example", "example", "https://t.me/id2757542991"])
    async def test_channel_is_searched_as_given(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock, query: str
    ) -> None:
        script(fragment)

        result = await client.giveaway_premium(query, 10)

        assert fragment.calls[0].data["query"] == query
        assert result.channel == query

    @pytest.mark.parametrize("fixture", ["giveaway_channel_not_found.json", "giveaway_not_a_channel.json"])
    async def test_not_a_channel_stops_before_the_page_opens(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock, fixture: str
    ) -> None:
        fragment.reply(ApiMethod.SEARCH_PREMIUM_GIVEAWAY_RECIPIENT, fixtures.response(fixture))

        with pytest.raises(ChannelNotFoundError, match="example"):
            await client.giveaway_premium("example", 10)

        assert fragment.methods == [ApiMethod.SEARCH_PREMIUM_GIVEAWAY_RECIPIENT]

    async def test_winner_count_fragment_refuses_is_raised_from_the_price_check(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock
    ) -> None:
        script(fragment, replies={PRICES: fixtures.response("giveaway_too_many_winners.json")})

        with pytest.raises(AboveMaximumError) as exc_info:
            await client.giveaway_premium("example", 10)

        assert exc_info.value.maximum == 5
        assert ApiMethod.INIT_GIVEAWAY_PREMIUM_REQUEST not in fragment.methods
        paid.assert_not_awaited()

    async def test_invoice_reply_without_request_id_is_not_paid(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock
    ) -> None:
        script(fragment, replies={ApiMethod.INIT_GIVEAWAY_PREMIUM_REQUEST: {"amount": "0.1"}})

        with pytest.raises(FragmentAPIError):
            await client.giveaway_premium("example", 10)

        paid.assert_not_awaited()

    async def test_verification_required(self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock) -> None:
        script(fragment, replies={ApiMethod.GET_GIVEAWAY_PREMIUM_LINK: {"need_verify": True}})

        with pytest.raises(VerificationError):
            await client.giveaway_premium("example", 10)

        paid.assert_not_awaited()


class TestPremiumGiveawayResultRepr:
    def test_shows_the_months_per_winner(self) -> None:
        result = PremiumGiveawayResult(
            transaction_id=TX_HASH, confirmed=True, comment=COMMENT, boc=TX_BOC, channel="example", winners=10, amount=6
        )

        assert repr(result) == (
            f"PremiumGiveawayResult(channel='example', winners=10, amount=6 months per winner, tx='{TX_HASH}', confirmed=True)"
        )
