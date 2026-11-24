"""Gifting Premium: the package list, the recipient check and the whole purchase flow."""

import re
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock

import pytest

from pyfragment import (
    AlreadySubscribedError,
    ConfigurationError,
    FragmentAPIError,
    FragmentClient,
    ParseError,
    PremiumResult,
    UserNotFoundError,
)
from pyfragment.constants.fragment import PREMIUM_PAGE
from pyfragment.domains.purchases.premium import PREMIUM_FLOW
from pyfragment.enums import ApiMethod, PaymentMethod
from tests.domains.purchase_script import CONFIRM_METHOD, script_purchase
from tests.support import fixtures
from tests.support.data import COMMENT, RECIPIENT_TOKEN, REQ_ID, TX_BOC, TX_HASH
from tests.support.fake_fragment import FakeFragment

FOUND = (ApiMethod.SEARCH_PREMIUM_GIFT_RECIPIENT, fixtures.response("stars_recipient_found.json"))
STATE = ApiMethod.UPDATE_PREMIUM_STATE
ALREADY_SUBSCRIBED = fixtures.response("premium_recipient_already_subscribed.json")


def script(fragment: FakeFragment, confirmed: bool = True, replies: dict[str, Any] | None = None) -> None:
    script_purchase(fragment, PREMIUM_FLOW, FOUND, confirmed, replies)


class TestGetPremiumPackages:
    async def test_options_of_the_gift_page(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.page(PREMIUM_PAGE, fixtures.html("premium_page_months.html"))

        packages = await client.get_premium_packages()

        assert [(p.months, p.gram, p.usd) for p in packages] == [
            (12, Decimal("29.66"), Decimal("28.99")),
            (6, Decimal("16.36"), Decimal("15.99")),
            (3, Decimal("12.27"), Decimal("11.99")),
        ]
        assert fragment.fetched == [PREMIUM_PAGE]

    async def test_page_without_options_is_a_parse_error(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.page(PREMIUM_PAGE, "<html></html>")

        with pytest.raises(ParseError):
            await client.get_premium_packages()


class TestCheckPremiumRecipient:
    async def test_default_duration_is_three_months(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(*FOUND)

        recipient = await client.check_premium_recipient("example")

        assert recipient.recipient == RECIPIENT_TOKEN
        [call] = fragment.calls
        assert (call.method, call.data, call.page_url) == (
            ApiMethod.SEARCH_PREMIUM_GIFT_RECIPIENT,
            {"query": "example", "months": 3},
            PREMIUM_PAGE,
        )

    async def test_user_with_premium(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(ApiMethod.SEARCH_PREMIUM_GIFT_RECIPIENT, ALREADY_SUBSCRIBED)

        with pytest.raises(AlreadySubscribedError):
            await client.check_premium_recipient("example", 6)

    async def test_invalid_months_is_rejected_before_any_call(self, client: FragmentClient, fragment: FakeFragment) -> None:
        with pytest.raises(ConfigurationError, match=re.escape(ConfigurationError.INVALID_MONTHS)):
            await client.check_premium_recipient("example", 4)

        assert fragment.calls == []


class TestPurchasePremium:
    async def test_whole_flow_in_fragments_order(self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock) -> None:
        script(fragment)

        result = await client.purchase_premium("example", 6)

        assert fragment.methods == [
            ApiMethod.SEARCH_PREMIUM_GIFT_RECIPIENT,
            STATE,
            ApiMethod.INIT_GIFT_PREMIUM_REQUEST,
            ApiMethod.GET_GIFT_PREMIUM_LINK,
            CONFIRM_METHOD,
            STATE,
        ]
        assert {call.page_url for call in fragment.calls} == {PREMIUM_PAGE}
        assert result == PremiumResult(
            transaction_id=TX_HASH, confirmed=True, comment=COMMENT, boc=TX_BOC, username="example", amount=6
        )

    async def test_request_payloads(self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock) -> None:
        script(fragment)

        await client.purchase_premium("example", 12)

        assert fragment.calls[0].data == {"query": "example", "months": 12}
        assert fragment.sent(ApiMethod.INIT_GIFT_PREMIUM_REQUEST)[0].data == {
            "recipient": RECIPIENT_TOKEN,
            "months": 12,
            "payment_method": PaymentMethod.GRAM,
        }
        assert fragment.sent(ApiMethod.GET_GIFT_PREMIUM_LINK)[0].data == {"transaction": 1, "id": REQ_ID, "show_sender": 1}

    @pytest.mark.parametrize(("show_sender", "sent"), [(True, 1), (False, 0)])
    async def test_show_sender_is_sent_as_a_flag(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock, show_sender: bool, sent: int
    ) -> None:
        script(fragment)

        await client.purchase_premium("example", 3, show_sender=show_sender)

        assert fragment.sent(ApiMethod.GET_GIFT_PREMIUM_LINK)[0].data["show_sender"] == sent

    async def test_usdt_payment_reaches_the_invoice_and_the_transfer(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock
    ) -> None:
        script(fragment)

        await client.purchase_premium("example", 6, payment_method=PaymentMethod.USDT_GRAM)

        assert fragment.sent(ApiMethod.INIT_GIFT_PREMIUM_REQUEST)[0].data["payment_method"] == PaymentMethod.USDT_GRAM
        assert paid.await_args is not None
        assert paid.await_args.kwargs == {"payment_method": PaymentMethod.USDT_GRAM, "req_id": REQ_ID}

    async def test_unconfirmed_when_fragment_never_reports_done(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock
    ) -> None:
        script(fragment, confirmed=False)
        client.confirm_timeout = 0.02

        result = await client.purchase_premium("example", 6)

        assert result.confirmed is False
        assert result.transaction_id == TX_HASH

    @pytest.mark.parametrize("months", [0, 1, 4, 24, "6", True])
    async def test_unsupported_duration_is_rejected_before_any_call(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock, months: Any
    ) -> None:
        with pytest.raises(ConfigurationError, match=re.escape(ConfigurationError.INVALID_MONTHS)):
            await client.purchase_premium("example", months)

        assert fragment.calls == []

    async def test_float_duration_is_rejected_before_any_call(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock
    ) -> None:
        with pytest.raises(ConfigurationError, match=re.escape(ConfigurationError.INVALID_MONTHS)):
            await client.purchase_premium("example", 6.0)  # type: ignore[arg-type]

        assert fragment.calls == []

    @pytest.mark.parametrize("payment_method", ["btc", "usdt_eth", "usdc_base"])
    async def test_payment_method_it_cannot_sign_for_is_rejected_before_any_call(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock, payment_method: Any
    ) -> None:
        with pytest.raises(ConfigurationError, match="Invalid payment method"):
            await client.purchase_premium("example", 6, payment_method=payment_method)

        assert fragment.calls == []

    @pytest.mark.parametrize("query", ["@example", "example", "https://t.me/example"])
    async def test_username_is_searched_as_given(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock, query: str
    ) -> None:
        script(fragment)

        result = await client.purchase_premium(query, 6)

        assert fragment.calls[0].data["query"] == query
        assert result.username == query

    async def test_unknown_user_stops_before_the_page_opens(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock
    ) -> None:
        fragment.reply(ApiMethod.SEARCH_PREMIUM_GIFT_RECIPIENT, fixtures.response("stars_recipient_not_found.json"))

        with pytest.raises(UserNotFoundError):
            await client.purchase_premium("example", 6)

        assert fragment.methods == [ApiMethod.SEARCH_PREMIUM_GIFT_RECIPIENT]

    @pytest.mark.parametrize("stage", [ApiMethod.SEARCH_PREMIUM_GIFT_RECIPIENT, ApiMethod.INIT_GIFT_PREMIUM_REQUEST])
    async def test_subscribed_user_is_refused_without_paying(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock, stage: ApiMethod
    ) -> None:
        script(fragment, replies={stage: ALREADY_SUBSCRIBED})

        with pytest.raises(AlreadySubscribedError):
            await client.purchase_premium("example", 6)

        paid.assert_not_awaited()

    async def test_fragment_error_at_the_link_is_raised_without_paying(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock
    ) -> None:
        script(fragment, replies={ApiMethod.GET_GIFT_PREMIUM_LINK: {"error": "Access denied"}})

        with pytest.raises(FragmentAPIError, match="Access denied"):
            await client.purchase_premium("example", 6)

        paid.assert_not_awaited()


class TestPremiumResultRepr:
    def test_shows_what_was_bought_and_whether_it_is_confirmed(self) -> None:
        result = PremiumResult(
            transaction_id=TX_HASH, confirmed=False, comment=COMMENT, boc=TX_BOC, username="example", amount=6
        )

        assert repr(result) == f"PremiumResult(username='example', amount=6 months, tx='{TX_HASH}', confirmed=False)"
