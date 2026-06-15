"""Verify wallet inspection returns friendly GRAM (ex TON) and USDT balances from Tonapi."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pyfragment import FragmentClient, WalletInfo
from tests.shared import FAKE_ADDRESS, FAKE_BALANCE_NANOGRAM

# Wallet mocked tests (GRAM and USDT balances are returned separately)


@pytest.mark.asyncio
async def test_get_wallet_returns_wallet_info(client: FragmentClient) -> None:
    mock_wallet = MagicMock()
    mock_wallet.refresh = AsyncMock()
    mock_wallet.balance = FAKE_BALANCE_NANOGRAM
    mock_wallet.state = MagicMock(value="active")
    mock_wallet.address.to_str.return_value = FAKE_ADDRESS

    with (
        patch("pyfragment.services.tonapi.account._make_ton_client") as mock_tonapi,
        patch("pyfragment.services.tonapi.account.WALLET_CLASSES") as mock_classes,
        patch("pyfragment.services.tonapi.account.get_usdt_balance", AsyncMock(return_value=12.3456)),
    ):
        mock_tonapi.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_tonapi.return_value.__aexit__ = AsyncMock(return_value=False)  # _make_ton_client returns context manager
        mock_classes["V5R1"].from_mnemonic.return_value = (mock_wallet, MagicMock(), None, None)

        result = await client.get_wallet()

    assert isinstance(result, WalletInfo)
    assert result.address == FAKE_ADDRESS
    assert result.state == "active"
    assert result.gram_balance == round(FAKE_BALANCE_NANOGRAM / 1_000_000_000, 4)
    assert result.usdt_balance == 12.3456


@pytest.mark.asyncio
async def test_get_wallet_balance_is_zero(client: FragmentClient) -> None:
    mock_wallet = MagicMock()
    mock_wallet.refresh = AsyncMock()
    mock_wallet.balance = 0
    mock_wallet.state = MagicMock(value="uninit")
    mock_wallet.address.to_str.return_value = FAKE_ADDRESS

    with (
        patch("pyfragment.services.tonapi.account._make_ton_client") as mock_tonapi,
        patch("pyfragment.services.tonapi.account.WALLET_CLASSES") as mock_classes,
        patch("pyfragment.services.tonapi.account.get_usdt_balance", AsyncMock(return_value=0.0)),
    ):
        mock_tonapi.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_tonapi.return_value.__aexit__ = AsyncMock(return_value=False)  # _make_ton_client returns context manager
        mock_classes["V5R1"].from_mnemonic.return_value = (mock_wallet, MagicMock(), None, None)

        result = await client.get_wallet()

    assert result.gram_balance == 0.0
    assert result.usdt_balance == 0.0
    assert result.state == "uninit"
