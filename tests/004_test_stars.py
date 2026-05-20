"""Cover stars purchase and giveaway flows, including validation and request wiring."""

import importlib
from unittest.mock import AsyncMock, patch

import pytest

_purchase_stars_mod = importlib.import_module("pyfragment.domains.purchases.purchase")
_giveaway_stars_mod = importlib.import_module("pyfragment.domains.giveaways.giveaway")
from pyfragment import ConfigurationError, FragmentClient, StarsGiveawayResult, StarsResult, UserNotFoundError
from tests.shared import FAKE_ACCOUNT, FAKE_RECIPIENT, FAKE_REQ_ID, FAKE_TRANSACTION, FAKE_TX_HASH

# Stars purchase validation tests


@pytest.mark.asyncio
async def test_purchase_stars_amount_too_low(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.purchase_stars("@user", amount=49)


@pytest.mark.asyncio
async def test_purchase_stars_amount_too_high(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.purchase_stars("@user", amount=1_000_001)


@pytest.mark.asyncio
async def test_purchase_stars_float_amount(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.purchase_stars("@user", amount=100.5)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_purchase_stars_invalid_payment_method(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError, match="Invalid payment method"):
        await client.purchase_stars("@user", amount=500, payment_method="btc")  # type: ignore[arg-type]


# Stars purchase mocked tests


@pytest.mark.asyncio
async def test_purchase_stars_success(client: FragmentClient) -> None:
    call_mock = AsyncMock(
        side_effect=[
            {"found": {"recipient": FAKE_RECIPIENT}},
            {},  # updateStarsBuyState
            {"req_id": FAKE_REQ_ID},
            FAKE_TRANSACTION,
        ]
    )
    with (
        patch.object(client, "call", call_mock),
        patch.object(_purchase_stars_mod, "get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
        patch.object(_purchase_stars_mod, "process_transaction", AsyncMock(return_value=FAKE_TX_HASH)),
    ):
        result = await client.purchase_stars("@user", amount=500)

    assert isinstance(result, StarsResult)
    assert result.transaction_id == FAKE_TX_HASH
    assert result.username == "@user"
    assert result.amount == 500


@pytest.mark.asyncio
async def test_purchase_stars_passes_payment_method(client: FragmentClient) -> None:
    call_mock = AsyncMock(
        side_effect=[
            {"found": {"recipient": FAKE_RECIPIENT}},
            {},  # updateStarsBuyState
            {"req_id": FAKE_REQ_ID},
            FAKE_TRANSACTION,
        ]
    )
    proc_mock = AsyncMock(return_value=FAKE_TX_HASH)
    with (
        patch.object(client, "call", call_mock),
        patch.object(_purchase_stars_mod, "get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
        patch.object(_purchase_stars_mod, "process_transaction", proc_mock),
    ):
        await client.purchase_stars("@user", amount=500, payment_method="usdt_ton")

    init_call = call_mock.await_args_list[2]
    assert init_call.args[0] == "initBuyStarsRequest"
    assert init_call.args[1]["payment_method"] == "usdt_ton"
    assert proc_mock.await_args is not None
    assert proc_mock.await_args.kwargs["payment_method"] == "usdt_ton"


@pytest.mark.asyncio
@pytest.mark.parametrize("query", ["@user", "monk", "https://t.me/monk"])
async def test_purchase_stars_accepts_query_formats(client: FragmentClient, query: str) -> None:
    call_mock = AsyncMock(return_value={"found": {}})
    with patch.object(client, "call", call_mock):
        with pytest.raises(UserNotFoundError):
            await client.purchase_stars(query, amount=500)

    search_call = call_mock.await_args_list[0]
    assert search_call.args[0] == "searchStarsRecipient"
    assert search_call.args[1]["query"] == query


@pytest.mark.asyncio
async def test_purchase_stars_user_not_found(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(return_value={"found": {}})):
        with pytest.raises(UserNotFoundError):
            await client.purchase_stars("@ghost", amount=500)


# Stars giveaway validation tests


@pytest.mark.asyncio
async def test_giveaway_stars_winners_too_low(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.giveaway_stars("@channel", winners=0, amount=500)


@pytest.mark.asyncio
async def test_giveaway_stars_winners_too_high(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.giveaway_stars("@channel", winners=6, amount=500)


@pytest.mark.asyncio
async def test_giveaway_stars_amount_too_low(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.giveaway_stars("@channel", winners=1, amount=499)


@pytest.mark.asyncio
async def test_giveaway_stars_amount_too_high(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.giveaway_stars("@channel", winners=1, amount=1_000_001)


@pytest.mark.asyncio
async def test_giveaway_stars_float_winners(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.giveaway_stars("@channel", winners=1.5, amount=500)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_giveaway_stars_float_amount(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.giveaway_stars("@channel", winners=1, amount=500.5)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_giveaway_stars_invalid_payment_method(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError, match="Invalid payment method"):
        await client.giveaway_stars("@channel", winners=1, amount=500, payment_method="btc")  # type: ignore[arg-type]


# Stars giveaway mocked tests


@pytest.mark.asyncio
async def test_giveaway_stars_success(client: FragmentClient) -> None:
    with (
        patch.object(
            client,
            "call",
            AsyncMock(
                side_effect=[
                    {"found": {"recipient": FAKE_RECIPIENT}},
                    {"req_id": FAKE_REQ_ID},
                    FAKE_TRANSACTION,
                ]
            ),
        ),
        patch.object(_giveaway_stars_mod, "get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
        patch.object(_giveaway_stars_mod, "process_transaction", AsyncMock(return_value=FAKE_TX_HASH)),
    ):
        result = await client.giveaway_stars("@channel", winners=3, amount=1000)

    assert isinstance(result, StarsGiveawayResult)
    assert result.transaction_id == FAKE_TX_HASH
    assert result.channel == "@channel"
    assert result.winners == 3
    assert result.amount == 1000


@pytest.mark.asyncio
async def test_giveaway_stars_passes_payment_method(client: FragmentClient) -> None:
    call_mock = AsyncMock(
        side_effect=[
            {"found": {"recipient": FAKE_RECIPIENT}},
            {"req_id": FAKE_REQ_ID},
            FAKE_TRANSACTION,
        ]
    )
    proc_mock = AsyncMock(return_value=FAKE_TX_HASH)
    with (
        patch.object(client, "call", call_mock),
        patch.object(_giveaway_stars_mod, "get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
        patch.object(_giveaway_stars_mod, "process_transaction", proc_mock),
    ):
        await client.giveaway_stars("@channel", winners=3, amount=1000, payment_method="usdt_ton")

    init_call = call_mock.await_args_list[1]
    assert init_call.args[0] == "initGiveawayStarsRequest"
    assert init_call.args[1]["payment_method"] == "usdt_ton"
    assert proc_mock.await_args is not None
    assert proc_mock.await_args.kwargs["payment_method"] == "usdt_ton"


@pytest.mark.asyncio
@pytest.mark.parametrize("query", ["@channel", "monk", "https://t.me/id2757542991"])
async def test_giveaway_stars_accepts_query_formats(client: FragmentClient, query: str) -> None:
    call_mock = AsyncMock(return_value={"found": {}})
    with patch.object(client, "call", call_mock):
        with pytest.raises(UserNotFoundError):
            await client.giveaway_stars(query, winners=1, amount=500)

    search_call = call_mock.await_args_list[0]
    assert search_call.args[0] == "searchStarsGiveawayRecipient"
    assert search_call.args[1]["query"] == query


@pytest.mark.asyncio
async def test_giveaway_stars_channel_not_found(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(return_value={"found": {}})):
        with pytest.raises(UserNotFoundError):
            await client.giveaway_stars("@ghost", winners=1, amount=500)
