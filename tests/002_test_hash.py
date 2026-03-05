"""Tests for get_fragment_hash() — fetches a valid lowercase hex hash
from the fragment.com/stars/buy page source."""

import re

import pytest

from app.core.constants import BASE_HEADERS, STARS_PAGE
from app.utils.hash import get_fragment_hash


@pytest.mark.asyncio
async def test_hash_is_valid_hex(cookies: dict) -> None:
    result = await get_fragment_hash(cookies, BASE_HEADERS, STARS_PAGE)
    assert isinstance(result, str)
    assert len(result) >= 10, f"hash too short: {result!r}"
    assert re.fullmatch(r"[a-f0-9]+", result), f"not a hex string: {result!r}"
