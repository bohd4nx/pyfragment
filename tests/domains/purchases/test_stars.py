"""Buying Stars: the price and package lookups, the recipient check and the whole purchase flow."""

import re
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock

import pytest

from pyfragment import (
    AboveMaximumError,
    AmountError,
    BelowMinimumError,
    ConfigurationError,
    FragmentAPIError,
    FragmentClient,
    InvoiceExpiredError,
    ParseError,
    Recipient,
    SessionExpiredError,
    StarsResult,
    UserNotFoundError,
    VerificationError,
)
from pyfragment.constants.fragment import STARS_PAGE
from pyfragment.constants.limits import STARS_PURCHASE
from pyfragment.domains.purchases.stars import STARS_FLOW
from pyfragment.enums import ApiMethod, PaymentMethod
from tests.domains.purchase_script import CONFIRM_METHOD, script_purchase
from tests.support import fixtures
from tests.support.data import COMMENT, RECIPIENT_TOKEN, REQ_ID, SENT, TX_BOC, TX_HASH
from tests.support.fake_fragment import FakeFragment

OUT_OF_RANGE = ConfigurationError.OUT_OF_RANGE.format(
    label=STARS_PURCHASE.label, min=STARS_PURCHASE.min, max=STARS_PURCHASE.max
)
FOUND = (ApiMethod.SEARCH_STARS_RECIPIENT, fixtures.response("stars_recipient_found.json"))
STATE = ApiMethod.UPDATE_STARS_BUY_STATE


def script(fragment: FakeFragment, confirmed: bool = True, replies: dict[str, Any] | None = None) -> None:
    script_purchase(fragment, STARS_FLOW, FOUND, confirmed, replies)


class TestGetStarsPrice:
    async def test_price_in_gram(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(ApiMethod.UPDATE_STARS_PRICES, fixtures.response("stars_prices.json"))

        price = await client.get_stars_price(500)

        assert price == Decimal("0.7677")
        [call] = fragment.calls
        assert (call.method, call.data, call.page_url) == (ApiMethod.UPDATE_STARS_PRICES, {"quantity": 500}, STARS_PAGE)

    @pytest.mark.parametrize("amount", [STARS_PURCHASE.min - 1, STARS_PURCHASE.max + 1, 100.5, True])
    async def test_amount_out_of_range_is_rejected_before_any_call(
        self, client: FragmentClient, fragment: FakeFragment, amount: Any
    ) -> None:
        with pytest.raises(ConfigurationError, match=re.escape(OUT_OF_RANGE)):
            await client.get_stars_price(amount)

        assert fragment.calls == []

    @pytest.mark.parametrize(
        ("fixture", "error"),
        [
            ("stars_below_minimum.json", BelowMinimumError),
            ("stars_above_maximum.json", AboveMaximumError),
            ("stars_amount_range.json", AmountError),
        ],
    )
    async def test_fragment_refusing_the_amount_raises_its_typed_error(
        self, client: FragmentClient, fragment: FakeFragment, fixture: str, error: type[AmountError]
    ) -> None:
        fragment.reply(ApiMethod.UPDATE_STARS_PRICES, fixtures.response(fixture))

        with pytest.raises(error):
            await client.get_stars_price(500)

    async def test_the_minimum_a_recipient_asks_for_is_read_with_its_thousands_separator(
        self, client: FragmentClient, fragment: FakeFragment
    ) -> None:
        fragment.reply(ApiMethod.UPDATE_STARS_PRICES, {"error": "You can buy a minimum of 35,000 stars"})

        with pytest.raises(BelowMinimumError) as exc_info:
            await client.get_stars_price(50)

        assert exc_info.value.minimum == 35_000
        assert not exc_info.value.retryable

    async def test_unrecognised_error_is_a_plain_api_error(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(ApiMethod.UPDATE_STARS_PRICES, {"error": "Access denied"})

        with pytest.raises(FragmentAPIError, match="Access denied") as exc_info:
            await client.get_stars_price(50)

        assert type(exc_info.value) is FragmentAPIError

    @pytest.mark.parametrize("reply", [{"ok": True}, {"ok": True, "cur_price": ""}, {"cur_price": 'icon-ton">0</div>'}])
    async def test_reply_without_a_usable_price_is_a_parse_error(
        self, client: FragmentClient, fragment: FakeFragment, reply: dict[str, Any]
    ) -> None:
        fragment.reply(ApiMethod.UPDATE_STARS_PRICES, reply)

        with pytest.raises(ParseError):
            await client.get_stars_price(100)


class TestGetStarsPackages:
    async def test_packages_with_their_prices(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(ApiMethod.UPDATE_STARS_PRICES, fixtures.response("stars_prices.json"))

        packages = await client.get_stars_packages()

        assert (packages[0].stars, packages[0].gram, packages[0].usd) == (50, Decimal("0.7677"), Decimal("0.75"))
        assert len(packages) == 22

    async def test_asks_for_the_minimum_quantity(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(ApiMethod.UPDATE_STARS_PRICES, fixtures.response("stars_prices.json"))

        await client.get_stars_packages()

        [call] = fragment.calls
        assert (call.data, call.page_url) == ({"quantity": STARS_PURCHASE.min}, STARS_PAGE)

    async def test_fragment_error_is_raised(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(ApiMethod.UPDATE_STARS_PRICES, {"error": "Access denied"})

        with pytest.raises(FragmentAPIError, match="Access denied"):
            await client.get_stars_packages()

    @pytest.mark.parametrize("reply", [{"ok": True}, {"ok": True, "options_html": ""}])
    async def test_reply_without_packages_is_a_parse_error(
        self, client: FragmentClient, fragment: FakeFragment, reply: dict[str, Any]
    ) -> None:
        fragment.reply(ApiMethod.UPDATE_STARS_PRICES, reply)

        with pytest.raises(ParseError):
            await client.get_stars_packages()


class TestCheckStarsRecipient:
    async def test_found_user_is_returned_and_nothing_is_bought(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(*FOUND)

        recipient = await client.check_stars_recipient("example")

        assert isinstance(recipient, Recipient)
        assert recipient.recipient == RECIPIENT_TOKEN
        assert fragment.methods == [ApiMethod.SEARCH_STARS_RECIPIENT]

    async def test_unknown_user(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(ApiMethod.SEARCH_STARS_RECIPIENT, fixtures.response("stars_recipient_not_found.json"))

        with pytest.raises(UserNotFoundError):
            await client.check_stars_recipient("example")


class TestPurchaseStars:
    async def test_whole_flow_in_fragments_order(self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock) -> None:
        script(fragment)

        result = await client.purchase_stars("example", 500)

        assert fragment.methods == [
            ApiMethod.SEARCH_STARS_RECIPIENT,
            STATE,
            ApiMethod.INIT_BUY_STARS_REQUEST,
            ApiMethod.GET_BUY_STARS_LINK,
            CONFIRM_METHOD,
            STATE,
        ]
        assert {call.page_url for call in fragment.calls} == {STARS_PAGE}
        assert result == StarsResult(
            transaction_id=TX_HASH, confirmed=True, comment=COMMENT, boc=TX_BOC, username="example", amount=500
        )

    async def test_request_payloads(self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock) -> None:
        script(fragment)

        await client.purchase_stars("example", 500)

        assert fragment.calls[0].data == {"query": "example", "quantity": ""}
        assert fragment.sent(ApiMethod.INIT_BUY_STARS_REQUEST)[0].data == {
            "recipient": RECIPIENT_TOKEN,
            "quantity": 500,
            "payment_method": PaymentMethod.GRAM,
        }
        assert fragment.sent(ApiMethod.GET_BUY_STARS_LINK)[0].data == {"transaction": 1, "id": REQ_ID, "show_sender": 1}

    @pytest.mark.parametrize(("show_sender", "sent"), [(True, 1), (False, 0)])
    async def test_show_sender_is_sent_as_a_flag(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock, show_sender: bool, sent: int
    ) -> None:
        script(fragment)

        await client.purchase_stars("example", 500, show_sender=show_sender)

        assert fragment.sent(ApiMethod.GET_BUY_STARS_LINK)[0].data["show_sender"] == sent

    @pytest.mark.parametrize("payment_method", list(PaymentMethod))
    async def test_payment_method_reaches_the_invoice_and_the_transfer(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock, payment_method: PaymentMethod
    ) -> None:
        script(fragment)

        await client.purchase_stars("example", 500, payment_method=payment_method)

        assert fragment.sent(ApiMethod.INIT_BUY_STARS_REQUEST)[0].data["payment_method"] == payment_method
        assert paid.await_args is not None
        assert paid.await_args.kwargs == {"payment_method": payment_method, "req_id": REQ_ID}

    async def test_signed_transaction_is_reported_back_to_fragment(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock
    ) -> None:
        script(fragment)

        await client.purchase_stars("example", 500)

        [report] = fragment.sent(CONFIRM_METHOD)
        assert report.data["boc"] == SENT.boc
        assert report.data["id"] == REQ_ID
        assert {"account", "device"} <= report.data.keys()

    async def test_unconfirmed_when_fragment_never_reports_done(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock
    ) -> None:
        script(fragment, confirmed=False)
        client.confirm_timeout = 0.02

        result = await client.purchase_stars("example", 500)

        assert result.confirmed is False
        assert result.transaction_id == TX_HASH

    async def test_unconfirmed_when_reporting_fails(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock
    ) -> None:
        script(fragment, replies={CONFIRM_METHOD: FragmentAPIError("boom")})

        result = await client.purchase_stars("example", 500)

        assert result.confirmed is False
        assert result.boc == TX_BOC

    async def test_zero_confirm_timeout_skips_waiting(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock
    ) -> None:
        script(fragment)
        client.confirm_timeout = 0

        result = await client.purchase_stars("example", 500)

        assert result.confirmed is False
        assert fragment.methods.count(STATE) == 1

    @pytest.mark.parametrize("amount", [STARS_PURCHASE.min - 1, STARS_PURCHASE.max + 1, 100.5, True])
    async def test_amount_out_of_range_is_rejected_before_any_call(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock, amount: Any
    ) -> None:
        with pytest.raises(ConfigurationError, match=re.escape(OUT_OF_RANGE)):
            await client.purchase_stars("example", amount)

        assert fragment.calls == []

    @pytest.mark.parametrize("payment_method", ["btc", "usdt_eth", "usdt_pol", "usdc_eth", "usdc_base", "usdc_pol"])
    async def test_payment_method_it_cannot_sign_for_is_rejected_before_any_call(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock, payment_method: Any
    ) -> None:
        with pytest.raises(ConfigurationError, match="Invalid payment method"):
            await client.purchase_stars("example", 500, payment_method=payment_method)

        assert fragment.calls == []

    @pytest.mark.parametrize("query", ["@example", "example", "https://t.me/example"])
    async def test_username_is_searched_as_given(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock, query: str
    ) -> None:
        script(fragment)

        result = await client.purchase_stars(query, 500)

        assert fragment.calls[0].data["query"] == query
        assert result.username == query

    async def test_unknown_user_stops_before_the_page_opens(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock
    ) -> None:
        fragment.reply(ApiMethod.SEARCH_STARS_RECIPIENT, fixtures.response("stars_recipient_not_found.json"))

        with pytest.raises(UserNotFoundError, match="example"):
            await client.purchase_stars("example", 500)

        assert fragment.methods == [ApiMethod.SEARCH_STARS_RECIPIENT]

    async def test_amount_below_the_recipients_minimum_is_raised_from_the_invoice(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock
    ) -> None:
        script(fragment, replies={ApiMethod.INIT_BUY_STARS_REQUEST: fixtures.response("stars_below_minimum.json")})

        with pytest.raises(BelowMinimumError) as exc_info:
            await client.purchase_stars("example", 50)

        assert exc_info.value.minimum == STARS_PURCHASE.min
        paid.assert_not_awaited()

    async def test_session_without_a_wallet(self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock) -> None:
        script(fragment, replies={ApiMethod.INIT_BUY_STARS_REQUEST: {"need_ton": True}})

        with pytest.raises(SessionExpiredError, match="stel_ton_token"):
            await client.purchase_stars("example", 500)

        paid.assert_not_awaited()

    async def test_invoice_reply_without_request_id(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock
    ) -> None:
        script(fragment, replies={ApiMethod.INIT_BUY_STARS_REQUEST: {"amount": "0.1"}})

        with pytest.raises(SessionExpiredError):
            await client.purchase_stars("example", 500)

        paid.assert_not_awaited()

    async def test_verification_required(self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock) -> None:
        script(fragment, replies={ApiMethod.GET_BUY_STARS_LINK: {"need_verify": True}})

        with pytest.raises(VerificationError):
            await client.purchase_stars("example", 500)

        paid.assert_not_awaited()

    async def test_expired_invoice_is_retryable_and_costs_nothing(
        self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock
    ) -> None:
        script(fragment, replies={ApiMethod.GET_BUY_STARS_LINK: {"error": "Session expired"}})

        with pytest.raises(InvoiceExpiredError) as exc_info:
            await client.purchase_stars("example", 500)

        assert exc_info.value.retryable
        paid.assert_not_awaited()

    async def test_other_link_error_is_raised(self, client: FragmentClient, fragment: FakeFragment, paid: AsyncMock) -> None:
        script(fragment, replies={ApiMethod.GET_BUY_STARS_LINK: {"error": "Access denied"}})

        with pytest.raises(FragmentAPIError, match="Access denied"):
            await client.purchase_stars("example", 500)

        paid.assert_not_awaited()


class TestStarsResultRepr:
    def test_shows_what_was_bought_and_whether_it_is_confirmed(self) -> None:
        result = StarsResult(
            transaction_id=TX_HASH, confirmed=True, comment=COMMENT, boc=TX_BOC, username="example", amount=500
        )

        assert repr(result) == f"StarsResult(username='example', amount=500 stars, tx='{TX_HASH}', confirmed=True)"
