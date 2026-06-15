"""Cover premium purchase and giveaway flows, including validation and request wiring."""

from unittest.mock import AsyncMock, patch

import pytest

import pyfragment.domains.giveaways.giveaway as _giveaway_premium_mod
import pyfragment.domains.purchases.purchase as _purchase_premium_mod
from pyfragment import ConfigurationError, FragmentClient, PremiumGiveawayResult, PremiumResult, UserNotFoundError
from pyfragment.core.constants.limits import PREMIUM_MONTHS_VALID, PREMIUM_WINNERS_MAX, PREMIUM_WINNERS_MIN
from pyfragment.exceptions import AlreadySubscribedError
from pyfragment.enums import PaymentMethod
from tests.shared import FAKE_ACCOUNT, FAKE_RECIPIENT, FAKE_REQ_ID, FAKE_TRANSACTION, FAKE_TX_HASH

# Premium purchase validation tests


@pytest.mark.asyncio
async def test_purchase_premium_invalid_months(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.purchase_premium("@user", months=5)


@pytest.mark.asyncio
async def test_purchase_premium_months_zero(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.purchase_premium("@user", months=min(PREMIUM_MONTHS_VALID) - 1)


@pytest.mark.asyncio
async def test_purchase_premium_invalid_payment_method(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError, match="Invalid payment method"):
        await client.purchase_premium("@user", months=3, payment_method="btc")  # type: ignore[arg-type]


# Premium purchase mocked tests


@pytest.mark.asyncio
async def test_purchase_premium_success(client: FragmentClient) -> None:
    with (
        patch.object(
            client,
            "call",
            AsyncMock(
                side_effect=[
                    {"found": {"recipient": FAKE_RECIPIENT}},
                    {},  # updatePremiumState
                    {"req_id": FAKE_REQ_ID},
                    FAKE_TRANSACTION,
                ]
            ),
        ),
        patch.object(_purchase_premium_mod, "get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
        patch.object(_purchase_premium_mod, "process_transaction", AsyncMock(return_value=FAKE_TX_HASH)),
    ):
        result = await client.purchase_premium("@user", months=3)

    assert isinstance(result, PremiumResult)
    assert result.transaction_id == FAKE_TX_HASH
    assert result.username == "@user"
    assert result.amount == 3


@pytest.mark.asyncio
async def test_purchase_premium_passes_payment_method(client: FragmentClient) -> None:
    call_mock = AsyncMock(
        side_effect=[
            {"found": {"recipient": FAKE_RECIPIENT}},
            {},  # updatePremiumState
            {"req_id": FAKE_REQ_ID},
            FAKE_TRANSACTION,
        ]
    )
    proc_mock = AsyncMock(return_value=FAKE_TX_HASH)
    with (
        patch.object(client, "call", call_mock),
        patch.object(_purchase_premium_mod, "get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
        patch.object(_purchase_premium_mod, "process_transaction", proc_mock),
    ):
        await client.purchase_premium("@user", months=6, payment_method=PaymentMethod.USDT_GRAM)

    init_call = call_mock.await_args_list[2]
    assert init_call.args[0] == "initGiftPremiumRequest"
    assert init_call.args[1]["payment_method"] == "usdt_ton"
    assert proc_mock.await_args is not None
    assert proc_mock.await_args.kwargs["payment_method"] == "usdt_ton"


@pytest.mark.asyncio
async def test_purchase_premium_already_subscribed_raises(client: FragmentClient) -> None:
    with (
        patch.object(
            client,
            "call",
            AsyncMock(
                side_effect=[
                    {"found": {"recipient": FAKE_RECIPIENT}},
                    {},  # updatePremiumState
                    {"error": "This account is already subscribed to Telegram Premium."},
                ]
            ),
        ),
    ):
        with pytest.raises(AlreadySubscribedError):
            await client.purchase_premium("@user", months=6)


@pytest.mark.asyncio
@pytest.mark.parametrize("query", ["@user", "monk", "https://t.me/monk"])
async def test_purchase_premium_accepts_query_formats(client: FragmentClient, query: str) -> None:
    call_mock = AsyncMock(return_value={"found": {}})
    with patch.object(client, "call", call_mock):
        with pytest.raises(UserNotFoundError):
            await client.purchase_premium(query, months=6)

    search_call = call_mock.await_args_list[0]
    assert search_call.args[0] == "searchPremiumGiftRecipient"
    assert search_call.args[1]["query"] == query


@pytest.mark.asyncio
async def test_purchase_premium_user_not_found(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(return_value={"found": {}})):
        with pytest.raises(UserNotFoundError):
            await client.purchase_premium("@ghost", months=3)


# Premium giveaway validation tests


@pytest.mark.asyncio
async def test_giveaway_premium_winners_too_low(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.giveaway_premium("@channel", winners=PREMIUM_WINNERS_MIN - 1, months=3)


@pytest.mark.asyncio
async def test_giveaway_premium_winners_too_high(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.giveaway_premium("@channel", winners=PREMIUM_WINNERS_MAX + 1, months=3)


@pytest.mark.asyncio
async def test_giveaway_premium_float_winners(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.giveaway_premium("@channel", winners=2.5, months=3)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_giveaway_premium_invalid_months(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.giveaway_premium("@channel", winners=10, months=5)


@pytest.mark.asyncio
async def test_giveaway_premium_invalid_payment_method(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError, match="Invalid payment method"):
        await client.giveaway_premium("@channel", winners=10, months=3, payment_method="btc")  # type: ignore[arg-type]


# Premium giveaway mocked tests


@pytest.mark.asyncio
async def test_giveaway_premium_success(client: FragmentClient) -> None:
    with (
        patch.object(
            client,
            "call",
            AsyncMock(
                side_effect=[
                    {"found": {"recipient": FAKE_RECIPIENT}},
                    {},
                    {},
                    {"req_id": FAKE_REQ_ID},
                    FAKE_TRANSACTION,
                ]
            ),
        ),
        patch.object(_giveaway_premium_mod, "get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
        patch.object(_giveaway_premium_mod, "process_transaction", AsyncMock(return_value=FAKE_TX_HASH)),
    ):
        result = await client.giveaway_premium("@channel", winners=10, months=3)

    assert isinstance(result, PremiumGiveawayResult)
    assert result.transaction_id == FAKE_TX_HASH
    assert result.channel == "@channel"
    assert result.winners == 10
    assert result.amount == 3


@pytest.mark.asyncio
async def test_giveaway_premium_passes_payment_method(client: FragmentClient) -> None:
    call_mock = AsyncMock(
        side_effect=[
            {"found": {"recipient": FAKE_RECIPIENT}},
            {},
            {},
            {"req_id": FAKE_REQ_ID},
            FAKE_TRANSACTION,
        ]
    )
    proc_mock = AsyncMock(return_value=FAKE_TX_HASH)
    with (
        patch.object(client, "call", call_mock),
        patch.object(_giveaway_premium_mod, "get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
        patch.object(_giveaway_premium_mod, "process_transaction", proc_mock),
    ):
        await client.giveaway_premium("@channel", winners=10, months=6, payment_method=PaymentMethod.USDT_GRAM)

    init_call = call_mock.await_args_list[3]
    assert init_call.args[0] == "initGiveawayPremiumRequest"
    assert init_call.args[1]["payment_method"] == "usdt_ton"
    assert proc_mock.await_args is not None
    assert proc_mock.await_args.kwargs["payment_method"] == "usdt_ton"


@pytest.mark.asyncio
@pytest.mark.parametrize("query", ["@channel", "monk", "https://t.me/id2757542991"])
async def test_giveaway_premium_accepts_query_formats(client: FragmentClient, query: str) -> None:
    call_mock = AsyncMock(return_value={"found": {}})
    with patch.object(client, "call", call_mock):
        with pytest.raises(UserNotFoundError):
            await client.giveaway_premium(query, winners=10, months=3)

    search_call = call_mock.await_args_list[0]
    assert search_call.args[0] == "searchPremiumGiveawayRecipient"
    assert search_call.args[1]["query"] == query


@pytest.mark.asyncio
async def test_giveaway_premium_channel_not_found(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(return_value={"found": {}})):
        with pytest.raises(UserNotFoundError):
            await client.giveaway_premium("@ghost", winners=1, months=3)
