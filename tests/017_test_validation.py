"""Check numeric input validation for amounts, counts, and giveaway limits."""

import pytest

from pyfragment import ConfigurationError, FragmentClient
from pyfragment.core.constants import STARS_WINNERS_MAX
from pyfragment.core.validation import is_int_in_range

# is_int_in_range


@pytest.mark.parametrize(
    ("value", "expected"), [(1, True), (5, True), (0, False), (6, False), (True, False), (2.0, False), ("3", False)]
)
def test_is_int_in_range(value: object, expected: bool) -> None:
    assert is_int_in_range(value, 1, 5) is expected


# bool must not slip through as 1


@pytest.mark.asyncio
async def test_topup_gram_rejects_bool(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.topup_gram("@user", True)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_recharge_ads_rejects_bool(client: FragmentClient) -> None:
    with pytest.raises(ConfigurationError):
        await client.recharge_ads("@channel", True)  # type: ignore[arg-type]


# Stars giveaway: Fragment allows 1-5 winners


@pytest.mark.asyncio
@pytest.mark.parametrize("winners", [0, STARS_WINNERS_MAX + 1, 15, True])
async def test_giveaway_stars_rejects_invalid_winners(client: FragmentClient, winners: int) -> None:
    with pytest.raises(ConfigurationError, match="winners"):
        await client.giveaway_stars("@channel", winners, 500)


@pytest.mark.asyncio
@pytest.mark.parametrize("amount", [499, 1_000_001, True])
async def test_giveaway_stars_rejects_invalid_amount(client: FragmentClient, amount: int) -> None:
    with pytest.raises(ConfigurationError, match="Stars per winner"):
        await client.giveaway_stars("@channel", 1, amount)


@pytest.mark.asyncio
@pytest.mark.parametrize("winners", [0, 24_001, True])
async def test_giveaway_premium_rejects_invalid_winners(client: FragmentClient, winners: int) -> None:
    with pytest.raises(ConfigurationError, match="winners"):
        await client.giveaway_premium("@channel", winners)
