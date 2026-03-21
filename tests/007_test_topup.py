"""Unit tests for topup_ton — validation and mocked network calls."""

from unittest.mock import AsyncMock, patch

import pytest

from pyfragment import FragmentClient
from pyfragment.types import AdsTopupResult, ConfigurationError, UserNotFoundError
from tests.shared import FAKE_ACCOUNT, FAKE_HASH, FAKE_RECIPIENT, FAKE_REQ_ID, FAKE_TRANSACTION, FAKE_TX_HASH

# Topup TON validation tests


@pytest.mark.asyncio
async def test_topup_ton_amount_zero(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.topup_ton("@user", amount=0)


@pytest.mark.asyncio
async def test_topup_ton_amount_too_high(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.topup_ton("@user", amount=1_000_000_001)


@pytest.mark.asyncio
async def test_topup_ton_float_amount(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.topup_ton("@user", amount=1.5)  # type: ignore[arg-type]


# Topup TON mocked tests


@pytest.mark.asyncio
async def test_topup_ton_success(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.topup_ton.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.methods.topup_ton.get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
        patch(
            "pyfragment.methods.topup_ton.fragment_request",
            AsyncMock(
                side_effect=[
                    {},  # updateAdsTopupState
                    {"found": {"recipient": FAKE_RECIPIENT}},
                    {"req_id": FAKE_REQ_ID},
                ]
            ),
        ),
        patch("pyfragment.methods.topup_ton.execute_transaction_request", AsyncMock(return_value=FAKE_TRANSACTION)),
        patch("pyfragment.methods.topup_ton.process_transaction", AsyncMock(return_value=FAKE_TX_HASH)),
    ):
        result = await client.topup_ton("@user", amount=10)

    assert isinstance(result, AdsTopupResult)
    assert result.transaction_id == FAKE_TX_HASH
    assert result.username == "@user"
    assert result.amount == 10


@pytest.mark.asyncio
async def test_topup_ton_user_not_found(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.topup_ton.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.methods.topup_ton.get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
        patch(
            "pyfragment.methods.topup_ton.fragment_request",
            AsyncMock(side_effect=[{}, {"found": {}}]),
        ),
    ):
        with pytest.raises(UserNotFoundError):
            await client.topup_ton("@ghost", amount=10)
