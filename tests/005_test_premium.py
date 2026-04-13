"""Unit tests for Premium methods — purchase_premium and giveaway_premium."""

from unittest.mock import AsyncMock, patch

import pytest

from pyfragment import FragmentClient
from pyfragment.types import ConfigurationError, PremiumGiveawayResult, PremiumResult, UserNotFoundError
from tests.shared import FAKE_ACCOUNT, FAKE_RECIPIENT, FAKE_REQ_ID, FAKE_TRANSACTION, FAKE_TX_HASH

# Premium purchase validation tests


@pytest.mark.asyncio
async def test_purchase_premium_invalid_months(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.purchase_premium("@user", months=5)


@pytest.mark.asyncio
async def test_purchase_premium_months_zero(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.purchase_premium("@user", months=0)


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
        patch("pyfragment.methods.purchase_premium.get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
        patch("pyfragment.methods.purchase_premium.process_transaction", AsyncMock(return_value=FAKE_TX_HASH)),
    ):
        result = await client.purchase_premium("@user", months=3)

    assert isinstance(result, PremiumResult)
    assert result.transaction_id == FAKE_TX_HASH
    assert result.username == "@user"
    assert result.amount == 3


@pytest.mark.asyncio
async def test_purchase_premium_user_not_found(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(return_value={"found": {}})):
        with pytest.raises(UserNotFoundError):
            await client.purchase_premium("@ghost", months=3)


# Premium giveaway validation tests


@pytest.mark.asyncio
async def test_giveaway_premium_winners_too_low(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.giveaway_premium("@channel", winners=0, months=3)


@pytest.mark.asyncio
async def test_giveaway_premium_winners_too_high(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.giveaway_premium("@channel", winners=24_001, months=3)


@pytest.mark.asyncio
async def test_giveaway_premium_float_winners(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.giveaway_premium("@channel", winners=2.5, months=3)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_giveaway_premium_invalid_months(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.giveaway_premium("@channel", winners=10, months=5)


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
                    {"req_id": FAKE_REQ_ID},
                    FAKE_TRANSACTION,
                ]
            ),
        ),
        patch("pyfragment.methods.giveaway_premium.get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
        patch("pyfragment.methods.giveaway_premium.process_transaction", AsyncMock(return_value=FAKE_TX_HASH)),
    ):
        result = await client.giveaway_premium("@channel", winners=10, months=3)

    assert isinstance(result, PremiumGiveawayResult)
    assert result.transaction_id == FAKE_TX_HASH
    assert result.channel == "@channel"
    assert result.winners == 10
    assert result.amount == 3


@pytest.mark.asyncio
async def test_giveaway_premium_channel_not_found(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(return_value={"found": {}})):
        with pytest.raises(UserNotFoundError):
            await client.giveaway_premium("@ghost", winners=1, months=3)
