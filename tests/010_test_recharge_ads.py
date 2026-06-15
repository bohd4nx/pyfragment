"""Cover Telegram Ads recharge flow, including request preparation and KYC handling."""

from unittest.mock import AsyncMock, patch

import pytest

import pyfragment.domains.ads.recharge as _recharge_ads_mod
from pyfragment import AdsRechargeResult, ConfigurationError, FragmentClient
from pyfragment.core.constants import GRAM_TOPUP_MAX, GRAM_TOPUP_MIN
from tests.shared import FAKE_ACCOUNT, FAKE_ADS_ACCOUNT, FAKE_REQ_ID, FAKE_TRANSACTION, FAKE_TX_HASH

# recharge_ads validation tests


@pytest.mark.asyncio
async def test_recharge_ads_amount_zero(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.recharge_ads(FAKE_ADS_ACCOUNT, amount=GRAM_TOPUP_MIN - 1)


@pytest.mark.asyncio
async def test_recharge_ads_amount_too_high(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.recharge_ads(FAKE_ADS_ACCOUNT, amount=GRAM_TOPUP_MAX + 1)


@pytest.mark.asyncio
async def test_recharge_ads_float_amount(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.recharge_ads(FAKE_ADS_ACCOUNT, amount=5.5)  # type: ignore[arg-type]


# recharge_ads mocked tests


@pytest.mark.asyncio
async def test_recharge_ads_success(client: FragmentClient) -> None:
    with (
        patch.object(
            client,
            "call",
            AsyncMock(
                side_effect=[
                    {},  # updateAdsState
                    {"req_id": FAKE_REQ_ID},  # initAdsRechargeRequest
                    FAKE_TRANSACTION,  # getAdsRechargeLink
                ]
            ),
        ),
        patch.object(_recharge_ads_mod, "get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
        patch.object(_recharge_ads_mod, "process_transaction", AsyncMock(return_value=FAKE_TX_HASH)),
    ):
        result = await client.recharge_ads(FAKE_ADS_ACCOUNT, amount=10)

    assert isinstance(result, AdsRechargeResult)
    assert result.transaction_id == FAKE_TX_HASH
    assert result.amount == 10


# recharge_ads — error branches


@pytest.mark.asyncio
async def test_recharge_ads_missing_req_id_raises(client: FragmentClient) -> None:
    from pyfragment.exceptions import FragmentAPIError

    with (
        patch.object(
            client,
            "call",
            AsyncMock(
                side_effect=[
                    {},  # updateAdsState
                    {"amount": "0.1"},  # initAdsRechargeRequest — no req_id
                ]
            ),
        ),
        patch.object(_recharge_ads_mod, "get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
    ):
        with pytest.raises(FragmentAPIError):
            await client.recharge_ads(FAKE_ADS_ACCOUNT, amount=10)


@pytest.mark.asyncio
async def test_recharge_ads_need_verify_raises(client: FragmentClient) -> None:
    from pyfragment.exceptions import VerificationError

    with (
        patch.object(
            client,
            "call",
            AsyncMock(
                side_effect=[
                    {},  # updateAdsState
                    {"req_id": FAKE_REQ_ID},
                    {"need_verify": True},  # getAdsRechargeLink
                ]
            ),
        ),
        patch.object(_recharge_ads_mod, "get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
    ):
        with pytest.raises(VerificationError):
            await client.recharge_ads(FAKE_ADS_ACCOUNT, amount=10)
