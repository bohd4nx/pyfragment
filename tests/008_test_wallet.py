"""Unit tests for get_wallet — mocked network calls."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pyfragment import FragmentClient, WalletInfo

FAKE_ADDRESS = "UQCppfw5DxWgdVHf3zkmZS8k1mt9oAUYxQLwq2fz3nhO8No5"
FAKE_BALANCE_NANOTON = 1_500_000_000  # 1.5 TON


# Wallet mocked tests


@pytest.mark.asyncio
async def test_get_wallet_returns_wallet_info(client: FragmentClient) -> None:
    mock_wallet = MagicMock()
    mock_wallet.refresh = AsyncMock()
    mock_wallet.balance = FAKE_BALANCE_NANOTON
    mock_wallet.state = MagicMock(value="active")
    mock_wallet.address.to_str.return_value = FAKE_ADDRESS

    with (
        patch("pyfragment.utils.wallet.TonapiClient") as mock_tonapi,
        patch("pyfragment.utils.wallet.WALLET_CLASSES") as mock_classes,
    ):
        mock_tonapi.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_tonapi.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_classes["V5R1"].from_mnemonic.return_value = (mock_wallet, MagicMock(), None, None)

        result = await client.get_wallet()

    assert isinstance(result, WalletInfo)
    assert result.address == FAKE_ADDRESS
    assert result.state == "active"
    assert result.balance == round(FAKE_BALANCE_NANOTON / 1_000_000_000, 4)


@pytest.mark.asyncio
async def test_get_wallet_balance_is_zero(client: FragmentClient) -> None:
    mock_wallet = MagicMock()
    mock_wallet.refresh = AsyncMock()
    mock_wallet.balance = 0
    mock_wallet.state = MagicMock(value="uninit")
    mock_wallet.address.to_str.return_value = FAKE_ADDRESS

    with (
        patch("pyfragment.utils.wallet.TonapiClient") as mock_tonapi,
        patch("pyfragment.utils.wallet.WALLET_CLASSES") as mock_classes,
    ):
        mock_tonapi.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_tonapi.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_classes["V5R1"].from_mnemonic.return_value = (mock_wallet, MagicMock(), None, None)

        result = await client.get_wallet()

    assert result.balance == 0.0
    assert result.state == "uninit"
