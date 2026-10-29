"""Tests for get_premium_packages — parses Premium subscription options from the /premium/gift page."""

from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from pyfragment import FragmentAPIError, FragmentClient, PremiumPackage

# Minimal HTML containing the API hash (required by fetch_page) and three Premium packages.
_HASH_SNIPPET = 'src="\\/api?hash=abc123def456"'

FAKE_PREMIUM_HTML = f"""
<html><head></head><body>
  <script {_HASH_SNIPPET}></script>
  <div class="js-premium-options">
    <div class="tm-form-radio-items">
      <label class="tm-form-radio-item">
        <input type="radio" class="radio" name="months" value="12" checked>
        <div class="tm-form-radio-label">
          <div class="tm-radio-label">1 year<span class="tm-radio-label-badge">-52%</span></div>
          <div class="tm-value icon-before icon-ton">23<span class="mini-frac">.79</span></div>
          <div class="tm-radio-desc">&#036;28.99</div>
        </div>
      </label>
      <label class="tm-form-radio-item">
        <input type="radio" class="radio" name="months" value="6">
        <div class="tm-form-radio-label">
          <div class="tm-radio-label">6 months<span class="tm-radio-label-badge">-47%</span></div>
          <div class="tm-value icon-before icon-ton">13<span class="mini-frac">.12</span></div>
          <div class="tm-radio-desc">&#036;15.99</div>
        </div>
      </label>
      <label class="tm-form-radio-item">
        <input type="radio" class="radio" name="months" value="3">
        <div class="tm-form-radio-label">
          <div class="tm-radio-label">3 months<span class="tm-radio-label-badge">-20%</span></div>
          <div class="tm-value icon-before icon-ton">9<span class="mini-frac">.84</span></div>
          <div class="tm-radio-desc">&#036;11.99</div>
        </div>
      </label>
    </div>
  </div>
</body></html>
"""

EMPTY_PREMIUM_HTML = f"""
<html><head></head><body>
  <script {_HASH_SNIPPET}></script>
</body></html>
"""


@pytest.mark.asyncio
async def test_get_premium_packages_returns_all_options(client: FragmentClient) -> None:
    with patch.object(client._transport, "fetch_page", AsyncMock(return_value=FAKE_PREMIUM_HTML)):
        packages = await client.get_premium_packages()

    assert len(packages) == 3
    assert all(isinstance(p, PremiumPackage) for p in packages)


@pytest.mark.asyncio
async def test_get_premium_packages_correct_values(client: FragmentClient) -> None:
    with patch.object(client._transport, "fetch_page", AsyncMock(return_value=FAKE_PREMIUM_HTML)):
        packages = await client.get_premium_packages()

    pkg_12 = next(p for p in packages if p.months == 12)
    assert pkg_12.gram == Decimal("23.79")
    assert pkg_12.usd == Decimal("28.99")

    pkg_6 = next(p for p in packages if p.months == 6)
    assert pkg_6.gram == Decimal("13.12")
    assert pkg_6.usd == Decimal("15.99")

    pkg_3 = next(p for p in packages if p.months == 3)
    assert pkg_3.gram == Decimal("9.84")
    assert pkg_3.usd == Decimal("11.99")


@pytest.mark.asyncio
async def test_get_premium_packages_fetches_premium_page(client: FragmentClient) -> None:
    mock_fetch = AsyncMock(return_value=FAKE_PREMIUM_HTML)
    with patch.object(client._transport, "fetch_page", mock_fetch):
        await client.get_premium_packages()

    mock_fetch.assert_called_once()
    url = mock_fetch.call_args[0][0]
    assert "premium/gift" in url


@pytest.mark.asyncio
async def test_get_premium_packages_raises_when_no_packages(client: FragmentClient) -> None:
    with patch.object(client._transport, "fetch_page", AsyncMock(return_value=EMPTY_PREMIUM_HTML)):
        with pytest.raises(FragmentAPIError):
            await client.get_premium_packages()
