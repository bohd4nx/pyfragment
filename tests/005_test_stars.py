"""Unit tests for purchase_stars and giveaway_stars — validation and mocked network calls."""

from unittest.mock import AsyncMock, patch

import pytest

from pyfragment import FragmentClient
from pyfragment.types import ConfigurationError, StarsGiveawayResult, StarsResult, UserNotFoundError
from tests.shared import FAKE_ACCOUNT, FAKE_HASH, FAKE_RECIPIENT, FAKE_REQ_ID, FAKE_TRANSACTION, FAKE_TX_HASH

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


# Stars purchase mocked tests


@pytest.mark.asyncio
async def test_purchase_stars_success(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.purchase_stars.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.methods.purchase_stars.get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
        patch(
            "pyfragment.methods.purchase_stars.fragment_request",
            AsyncMock(side_effect=[{"found": {"recipient": FAKE_RECIPIENT}}, {"req_id": FAKE_REQ_ID}]),
        ),
        patch("pyfragment.methods.purchase_stars.execute_transaction_request", AsyncMock(return_value=FAKE_TRANSACTION)),
        patch("pyfragment.methods.purchase_stars.process_transaction", AsyncMock(return_value=FAKE_TX_HASH)),
    ):
        result = await client.purchase_stars("@user", amount=500)

    assert isinstance(result, StarsResult)
    assert result.transaction_id == FAKE_TX_HASH
    assert result.username == "@user"
    assert result.amount == 500


@pytest.mark.asyncio
async def test_purchase_stars_user_not_found(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.purchase_stars.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.methods.purchase_stars.get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
        patch("pyfragment.methods.purchase_stars.fragment_request", AsyncMock(return_value={"found": {}})),
    ):
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


# Stars giveaway mocked tests


@pytest.mark.asyncio
async def test_giveaway_stars_success(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.giveaway_stars.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.methods.giveaway_stars.get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
        patch(
            "pyfragment.methods.giveaway_stars.fragment_request",
            AsyncMock(side_effect=[{"found": {"recipient": FAKE_RECIPIENT}}, {"req_id": FAKE_REQ_ID}]),
        ),
        patch("pyfragment.methods.giveaway_stars.execute_transaction_request", AsyncMock(return_value=FAKE_TRANSACTION)),
        patch("pyfragment.methods.giveaway_stars.process_transaction", AsyncMock(return_value=FAKE_TX_HASH)),
    ):
        result = await client.giveaway_stars("@channel", winners=3, amount=1000)

    assert isinstance(result, StarsGiveawayResult)
    assert result.transaction_id == FAKE_TX_HASH
    assert result.channel == "@channel"
    assert result.winners == 3
    assert result.amount == 1000


@pytest.mark.asyncio
async def test_giveaway_stars_channel_not_found(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.giveaway_stars.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.methods.giveaway_stars.get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
        patch("pyfragment.methods.giveaway_stars.fragment_request", AsyncMock(return_value={"found": {}})),
    ):
        with pytest.raises(UserNotFoundError):
            await client.giveaway_stars("@ghost", winners=1, amount=500)
