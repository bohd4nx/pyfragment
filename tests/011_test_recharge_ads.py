"""Unit tests for recharge_ads — self-service Telegram Ads recharge."""

from unittest.mock import AsyncMock, patch

import pytest

from pyfragment import FragmentClient
from pyfragment.types import AdsRechargeResult, ConfigurationError
from tests.shared import FAKE_ACCOUNT, FAKE_ADS_ACCOUNT, FAKE_HASH, FAKE_REQ_ID, FAKE_TRANSACTION, FAKE_TX_HASH

# recharge_ads validation tests


@pytest.mark.asyncio
async def test_recharge_ads_amount_zero(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.recharge_ads(FAKE_ADS_ACCOUNT, amount=0)


@pytest.mark.asyncio
async def test_recharge_ads_amount_too_high(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.recharge_ads(FAKE_ADS_ACCOUNT, amount=1_000_000_001)


@pytest.mark.asyncio
async def test_recharge_ads_float_amount(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.recharge_ads(FAKE_ADS_ACCOUNT, amount=5.5)  # type: ignore[arg-type]


# recharge_ads mocked tests


@pytest.mark.asyncio
async def test_recharge_ads_success(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.recharge_ads.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.methods.recharge_ads.get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
        patch(
            "pyfragment.methods.recharge_ads.fragment_request",
            AsyncMock(
                side_effect=[
                    {},  # updateAdsState
                    {"req_id": FAKE_REQ_ID},  # initAdsRechargeRequest
                ]
            ),
        ),
        patch("pyfragment.methods.recharge_ads.execute_transaction_request", AsyncMock(return_value=FAKE_TRANSACTION)),
        patch("pyfragment.methods.recharge_ads.process_transaction", AsyncMock(return_value=FAKE_TX_HASH)),
    ):
        result = await client.recharge_ads(FAKE_ADS_ACCOUNT, amount=10)

    assert isinstance(result, AdsRechargeResult)
    assert result.transaction_id == FAKE_TX_HASH
    assert result.amount == 10
