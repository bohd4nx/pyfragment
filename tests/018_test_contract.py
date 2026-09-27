"""Live contract checks: pyfragment's assumptions still match what fragment.com serves.

Skipped unless FRAGMENT_LIVE=1 (needs network; run weekly by the Contract workflow), so a change
on Fragment's side - a moved API hash, a new limit - shows up as a failing check, not a user bug.
"""

import os
import re
from collections.abc import AsyncIterator

import pytest
from curl_cffi.requests import AsyncSession

from pyfragment.core.constants import (
    ADS_TOPUP_PAGE,
    GIFTS_PAGE,
    NUMBERS_PAGE,
    PREMIUM_GIVEAWAY_PAGE,
    PREMIUM_MONTHS_VALID,
    PREMIUM_PAGE,
    PREMIUM_WINNERS_MAX,
    PREMIUM_WINNERS_MIN,
    STARS_GIVEAWAY_PAGE,
    STARS_PAGE,
    STARS_PURCHASE_MAX,
    STARS_PURCHASE_MIN,
    STARS_WINNERS_MAX,
    STARS_WINNERS_MIN,
)
from pyfragment.enums import PaymentMethod
from pyfragment.transport import get_fragment_hash

pytestmark = pytest.mark.skipif(os.environ.get("FRAGMENT_LIVE") != "1", reason="FRAGMENT_LIVE=1 not set")

PAGES = [STARS_PAGE, STARS_GIVEAWAY_PAGE, PREMIUM_PAGE, PREMIUM_GIVEAWAY_PAGE, ADS_TOPUP_PAGE, NUMBERS_PAGE, GIFTS_PAGE]


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    async with AsyncSession(impersonate="chrome", timeout=30) as live_session:
        yield live_session


async def _page(session: AsyncSession, url: str) -> str:
    return str((await session.get(url)).text)


def _quantity_range(html: str) -> tuple[int, int]:
    match = re.search(r'placeholder="Enter amount from ([\d,]+) to ([\d,]+)"', html)
    assert match, "quantity placeholder not found"
    low, high = (int(g.replace(",", "")) for g in match.groups())
    return low, high


@pytest.mark.parametrize("page_url", PAGES)
async def test_api_hash_is_discoverable(session: AsyncSession, page_url: str) -> None:
    assert await get_fragment_hash(session, page_url)


async def test_stars_purchase_limits(session: AsyncSession) -> None:
    assert _quantity_range(await _page(session, STARS_PAGE)) == (STARS_PURCHASE_MIN, STARS_PURCHASE_MAX)


async def test_stars_giveaway_winner_limits(session: AsyncSession) -> None:
    assert _quantity_range(await _page(session, STARS_GIVEAWAY_PAGE)) == (STARS_WINNERS_MIN, STARS_WINNERS_MAX)


async def test_premium_giveaway_winner_limits(session: AsyncSession) -> None:
    assert _quantity_range(await _page(session, PREMIUM_GIVEAWAY_PAGE)) == (PREMIUM_WINNERS_MIN, PREMIUM_WINNERS_MAX)


async def test_premium_durations(session: AsyncSession) -> None:
    html = await _page(session, PREMIUM_PAGE)
    months = {int(m) for m in re.findall(r'name="months"[^>]*value="(\d+)"', html)}
    assert months == PREMIUM_MONTHS_VALID


async def test_payment_methods_match_enum(session: AsyncSession) -> None:
    html = await _page(session, PREMIUM_PAGE)
    offered = set(re.findall(r'name="payment_method"[^>]*value="(\w+)"', html))
    assert offered == {m.value for m in PaymentMethod}
