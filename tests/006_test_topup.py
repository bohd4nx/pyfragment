"""Cover GRAM (ex TON) top-up through Telegram Ads, including recipient lookup and transaction building."""

from unittest.mock import AsyncMock, patch

import pytest

import pyfragment.domains.ads.tonup as _topup_gram_mod
from pyfragment import AdsTopupResult, ConfigurationError, FragmentClient, UserNotFoundError
from pyfragment.core.constants import GRAM_TOPUP_MAX, GRAM_TOPUP_MIN
from tests.shared import FAKE_ACCOUNT, FAKE_RECIPIENT, FAKE_REQ_ID, FAKE_TRANSACTION, FAKE_TX_HASH

# Topup GRAM (ex TON) validation tests


@pytest.mark.asyncio
async def test_topup_gram_amount_zero(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.topup_gram("@user", amount=GRAM_TOPUP_MIN - 1)


@pytest.mark.asyncio
async def test_topup_gram_amount_too_high(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.topup_gram("@user", amount=GRAM_TOPUP_MAX + 1)


@pytest.mark.asyncio
async def test_topup_gram_float_amount(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.topup_gram("@user", amount=1.5)  # type: ignore[arg-type]


# Topup GRAM (ex TON) mocked tests


@pytest.mark.asyncio
async def test_topup_gram_success(client: FragmentClient) -> None:
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
        patch.object(_topup_gram_mod, "get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
        patch.object(_topup_gram_mod, "process_transaction", AsyncMock(return_value=FAKE_TX_HASH)),
    ):
        result = await client.topup_gram("@user", amount=10)

    assert isinstance(result, AdsTopupResult)
    assert result.transaction_id == FAKE_TX_HASH
    assert result.username == "@user"
    assert result.amount == 10


@pytest.mark.asyncio
async def test_topup_gram_user_not_found(client: FragmentClient) -> None:
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
            await client.topup_gram("@ghost", amount=10)


# topup_gram — error branches


@pytest.mark.asyncio
async def test_topup_gram_missing_req_id_raises(client: FragmentClient) -> None:
    from pyfragment.exceptions import FragmentAPIError

    with (
        patch.object(
            client,
            "call",
            AsyncMock(
                side_effect=[
                    {},  # updateAdsTopupState
                    {"found": {"recipient": FAKE_RECIPIENT}},
                    {"amount": "0.1"},  # initAdsTopupRequest — no req_id
                ]
            ),
        ),
        patch.object(_topup_gram_mod, "get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
    ):
        with pytest.raises(FragmentAPIError):
            await client.topup_gram("@user", amount=10)


@pytest.mark.asyncio
async def test_topup_gram_need_verify_raises(client: FragmentClient) -> None:
    from pyfragment.exceptions import VerificationError

    with (
        patch.object(
            client,
            "call",
            AsyncMock(
                side_effect=[
                    {},  # updateAdsTopupState
                    {"found": {"recipient": FAKE_RECIPIENT}},
                    {"req_id": FAKE_REQ_ID},
                    {"need_verify": True},  # getAdsTopupLink
                ]
            ),
        ),
        patch.object(_topup_gram_mod, "get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
    ):
        with pytest.raises(VerificationError):
            await client.topup_gram("@user", amount=10)
