"""Tests for get_stars_price and get_stars_packages."""

from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from pyfragment import FragmentAPIError, FragmentClient, StarsPackage
from pyfragment.enums import ApiMethod

# Realistic cur_price HTML as Fragment returns it (integer + mini-frac span for GRAM, plain for USD).
_CUR_PRICE_HTML = (
    '        <div class="tm-value icon-before icon-usd">0.75</div>\n'
    '        <div class="tm-radio-desc wide-only icon-before icon-ton">'
    '0<span class="mini-frac">.6159</span></div>'
)
_CUR_PRICE_LARGE = (
    '        <div class="tm-value icon-before icon-usd">2,786</div>\n'
    '        <div class="tm-radio-desc wide-only icon-before icon-ton">'
    '2,288<span class="mini-frac">.01</span></div>'
)

_OPTIONS_HTML = """
  <div class="tm-form-radio-item-wrap">
    <label class="tm-form-radio-item">
      <input type="radio" class="radio" name="stars" value="50" checked>
      <div class="tm-form-radio-label">
        <div class="tm-value icon-before icon-usd">0.75</div>
        <div class="tm-radio-desc wide-only icon-before icon-ton">0<span class="mini-frac">.6159</span></div>
      </div>
    </label>
  </div>
  <div class="tm-form-radio-item-wrap">
    <label class="tm-form-radio-item">
      <input type="radio" class="radio" name="stars" value="100">
      <div class="tm-form-radio-label">
        <div class="tm-value icon-before icon-usd">1.50</div>
        <div class="tm-radio-desc wide-only icon-before icon-ton">1<span class="mini-frac">.2318</span></div>
      </div>
    </label>
  </div>
"""


# ── get_stars_price ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_stars_price_returns_decimal(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(return_value={"ok": True, "cur_price": _CUR_PRICE_HTML})):
        result = await client.get_stars_price(50)

    assert isinstance(result, Decimal)
    assert result == Decimal("0.6159")


@pytest.mark.asyncio
async def test_get_stars_price_large_price(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(return_value={"ok": True, "cur_price": _CUR_PRICE_LARGE})):
        result = await client.get_stars_price(25_000)

    assert result == Decimal("2288.01")


@pytest.mark.asyncio
async def test_get_stars_price_sends_correct_method_and_quantity(client: FragmentClient) -> None:
    mock_call = AsyncMock(return_value={"ok": True, "cur_price": _CUR_PRICE_HTML})
    with patch.object(client, "call", mock_call):
        await client.get_stars_price(500)

    mock_call.assert_called_once()
    method, data = mock_call.call_args[0]
    assert method == ApiMethod.UPDATE_STARS_PRICES
    assert data == {"quantity": 500}


@pytest.mark.asyncio
async def test_get_stars_price_raises_on_fragment_error(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(return_value={"error": "You can buy up to 10,000,000 stars"})):
        with pytest.raises(FragmentAPIError):
            await client.get_stars_price(50)


@pytest.mark.asyncio
async def test_get_stars_price_raises_on_missing_cur_price(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(return_value={"ok": True})):
        with pytest.raises(FragmentAPIError):
            await client.get_stars_price(100)


@pytest.mark.asyncio
async def test_get_stars_price_raises_on_empty_cur_price(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(return_value={"ok": True, "cur_price": ""})):
        with pytest.raises(FragmentAPIError):
            await client.get_stars_price(100)


@pytest.mark.asyncio
async def test_get_stars_price_rejects_amount_below_min(client: FragmentClient) -> None:
    from pyfragment import ConfigurationError

    with pytest.raises(ConfigurationError):
        await client.get_stars_price(1)


@pytest.mark.asyncio
async def test_get_stars_price_rejects_amount_above_max(client: FragmentClient) -> None:
    from pyfragment import ConfigurationError

    with pytest.raises(ConfigurationError):
        await client.get_stars_price(99_999_999)


# ── get_stars_packages ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_stars_packages_returns_packages(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(return_value={"ok": True, "options_html": _OPTIONS_HTML})):
        packages = await client.get_stars_packages()

    assert len(packages) == 2
    assert all(isinstance(p, StarsPackage) for p in packages)

    pkg = packages[0]
    assert pkg.stars == 50
    assert pkg.gram == Decimal("0.6159")
    assert pkg.usd == Decimal("0.75")

    pkg2 = packages[1]
    assert pkg2.stars == 100
    assert pkg2.gram == Decimal("1.2318")
    assert pkg2.usd == Decimal("1.50")


@pytest.mark.asyncio
async def test_get_stars_packages_sends_minimum_quantity(client: FragmentClient) -> None:
    mock_call = AsyncMock(return_value={"ok": True, "options_html": _OPTIONS_HTML})
    with patch.object(client, "call", mock_call):
        await client.get_stars_packages()

    _, data = mock_call.call_args[0]
    assert data["quantity"] == 50  # STARS_PURCHASE_MIN


@pytest.mark.asyncio
async def test_get_stars_packages_raises_on_fragment_error(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(return_value={"error": "Access denied"})):
        with pytest.raises(FragmentAPIError):
            await client.get_stars_packages()


@pytest.mark.asyncio
async def test_get_stars_packages_raises_on_empty_html(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(return_value={"ok": True, "options_html": ""})):
        with pytest.raises(FragmentAPIError):
            await client.get_stars_packages()


@pytest.mark.asyncio
async def test_get_stars_packages_raises_on_missing_options_html(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(return_value={"ok": True})):
        with pytest.raises(FragmentAPIError):
            await client.get_stars_packages()
