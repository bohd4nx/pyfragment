"""Unit tests for topup_ton — TON Ads balance top-up."""

import importlib
from unittest.mock import AsyncMock, patch

import pytest

_topup_ton_mod = importlib.import_module("pyfragment.methods.topup_ton")
from pyfragment import FragmentClient
from pyfragment.types import AdsTopupResult, ConfigurationError, UserNotFoundError
from tests.shared import FAKE_ACCOUNT, FAKE_RECIPIENT, FAKE_REQ_ID, FAKE_TRANSACTION, FAKE_TX_HASH

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
        patch.object(
            client,
            "call",
            AsyncMock(
                side_effect=[
                    {},  # updateAdsTopupState
                    {"found": {"recipient": FAKE_RECIPIENT}},
                    {"req_id": FAKE_REQ_ID},
                    FAKE_TRANSACTION,
                ]
            ),
        ),
        patch.object(_topup_ton_mod, "get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
        patch.object(_topup_ton_mod, "process_transaction", AsyncMock(return_value=FAKE_TX_HASH)),
    ):
        result = await client.topup_ton("@user", amount=10)

    assert isinstance(result, AdsTopupResult)
    assert result.transaction_id == FAKE_TX_HASH
    assert result.username == "@user"
    assert result.amount == 10


@pytest.mark.asyncio
async def test_topup_ton_user_not_found(client: FragmentClient) -> None:
    with patch.object(
        client,
        "call",
        AsyncMock(
            side_effect=[
                {},  # updateAdsTopupState
                {"found": {}},
            ]
        ),
    ):
        with pytest.raises(UserNotFoundError):
            await client.topup_ton("@ghost", amount=10)
