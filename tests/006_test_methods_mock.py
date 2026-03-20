"""Tests for purchase methods with all network calls mocked."""

from unittest.mock import AsyncMock, patch

import pytest

from pyfragment import FragmentClient
from pyfragment.types import AdsTopupResult, PremiumResult, StarsResult, UserNotFoundError

VALID_SEED = "abandon " * 23 + "about"
VALID_API_KEY = "A" * 68
VALID_COOKIES = {
    "stel_ssid": "x",
    "stel_dt": "x",
    "stel_token": "x",
    "stel_ton_token": "x",
}
FAKE_HASH = "abc123"
FAKE_RECIPIENT = "recipient_token"
FAKE_REQ_ID = "req_42"
FAKE_TX_HASH = "deadbeef" * 8
FAKE_ACCOUNT = {"address": "0:abc", "publicKey": "pub", "chain": "-239", "walletStateInit": "base64=="}
FAKE_TRANSACTION = {"transaction": {"messages": [{"address": "0:abc", "amount": "100000000", "payload": ""}]}}


@pytest.fixture
def client() -> FragmentClient:
    return FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES)


@pytest.mark.asyncio
async def test_purchase_stars_success(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.stars.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.methods.stars.get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
        patch(
            "pyfragment.methods.stars.fragment_post",
            AsyncMock(
                side_effect=[
                    {"found": {"recipient": FAKE_RECIPIENT}},  # searchStarsRecipient
                    {"req_id": FAKE_REQ_ID},  # initBuyStarsRequest
                ]
            ),
        ),
        patch("pyfragment.methods.stars.execute_transaction_request", AsyncMock(return_value=FAKE_TRANSACTION)),
        patch("pyfragment.methods.stars.process_transaction", AsyncMock(return_value=FAKE_TX_HASH)),
    ):
        result = await client.purchase_stars("testuser", amount=100)

    assert isinstance(result, StarsResult)
    assert result.transaction_id == FAKE_TX_HASH
    assert result.username == "testuser"
    assert result.stars == 100


@pytest.mark.asyncio
async def test_purchase_stars_user_not_found(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.stars.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.methods.stars.get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
        patch("pyfragment.methods.stars.fragment_post", AsyncMock(return_value={"found": {}})),
    ):
        with pytest.raises(UserNotFoundError):
            await client.purchase_stars("ghost", amount=100)


@pytest.mark.asyncio
async def test_purchase_premium_success(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.premium.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.methods.premium.get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
        patch(
            "pyfragment.methods.premium.fragment_post",
            AsyncMock(
                side_effect=[
                    {"found": {"recipient": FAKE_RECIPIENT}},  # searchPremiumGiftRecipient
                    {},  # updatePremiumState
                    {"req_id": FAKE_REQ_ID},  # initGiftPremiumRequest
                ]
            ),
        ),
        patch("pyfragment.methods.premium.execute_transaction_request", AsyncMock(return_value=FAKE_TRANSACTION)),
        patch("pyfragment.methods.premium.process_transaction", AsyncMock(return_value=FAKE_TX_HASH)),
    ):
        result = await client.purchase_premium("testuser", months=6)

    assert isinstance(result, PremiumResult)
    assert result.transaction_id == FAKE_TX_HASH
    assert result.username == "testuser"
    assert result.months == 6


@pytest.mark.asyncio
async def test_purchase_premium_user_not_found(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.premium.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.methods.premium.get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
        patch("pyfragment.methods.premium.fragment_post", AsyncMock(return_value={"found": {}})),
    ):
        with pytest.raises(UserNotFoundError):
            await client.purchase_premium("ghost", months=3)


@pytest.mark.asyncio
async def test_topup_ton_success(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.ton.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.methods.ton.get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
        patch(
            "pyfragment.methods.ton.fragment_post",
            AsyncMock(
                side_effect=[
                    {},  # updateAdsTopupState
                    {"found": {"recipient": FAKE_RECIPIENT}},  # searchAdsTopupRecipient
                    {"req_id": FAKE_REQ_ID},  # initAdsTopupRequest
                ]
            ),
        ),
        patch("pyfragment.methods.ton.execute_transaction_request", AsyncMock(return_value=FAKE_TRANSACTION)),
        patch("pyfragment.methods.ton.process_transaction", AsyncMock(return_value=FAKE_TX_HASH)),
    ):
        result = await client.topup_ton("testuser", amount=10)

    assert isinstance(result, AdsTopupResult)
    assert result.transaction_id == FAKE_TX_HASH
    assert result.username == "testuser"
    assert result.amount == 10


@pytest.mark.asyncio
async def test_topup_ton_user_not_found(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.ton.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.methods.ton.get_account_info", AsyncMock(return_value=FAKE_ACCOUNT)),
        patch(
            "pyfragment.methods.ton.fragment_post",
            AsyncMock(
                side_effect=[
                    {},  # updateAdsTopupState
                    {"found": {}},  # searchAdsTopupRecipient → not found
                ]
            ),
        ),
    ):
        with pytest.raises(UserNotFoundError):
            await client.topup_ton("ghost", amount=10)
