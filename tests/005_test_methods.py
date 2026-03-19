"""Unit tests for method-level input validation — no network calls."""

import pytest

from pyfragment import FragmentClient
from pyfragment.types import ConfigurationError

VALID_SEED = "abandon " * 23 + "about"
VALID_API_KEY = "A" * 68
VALID_COOKIES = {
    "stel_ssid": "x",
    "stel_dt": "x",
    "stel_token": "x",
    "stel_ton_token": "x",
}


@pytest.fixture
def client() -> FragmentClient:
    return FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES)


@pytest.mark.asyncio
async def test_purchase_premium_invalid_months_raises(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.purchase_premium("@user", months=5)


@pytest.mark.asyncio
async def test_purchase_premium_valid_months(client: FragmentClient) -> None:
    """Validation passes for 3/6/12 — network error expected, not ConfigurationError."""
    for months in (3, 6, 12):
        with pytest.raises(Exception) as exc_info:
            await client.purchase_premium("@user", months=months)
        assert not isinstance(exc_info.value, ConfigurationError)


@pytest.mark.asyncio
async def test_purchase_stars_amount_too_low_raises(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.purchase_stars("@user", amount=49)


@pytest.mark.asyncio
async def test_purchase_stars_amount_too_high_raises(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.purchase_stars("@user", amount=1_000_001)


@pytest.mark.asyncio
async def test_purchase_stars_float_raises(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.purchase_stars("@user", amount=100.5)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_topup_ton_amount_zero_raises(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.topup_ton("@user", amount=0)


@pytest.mark.asyncio
async def test_topup_ton_amount_too_high_raises(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.topup_ton("@user", amount=1_000_000_001)
