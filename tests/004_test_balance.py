"""Unit tests for process_transaction() — balance checks before broadcast."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pyfragment.types import WalletError
from pyfragment.utils.wallet import process_transaction

VALID_SEED = "abandon " * 23 + "about"

# Minimal transaction payload: 0.5 TON = 500_000_000 nanotons
TRANSACTION_DATA = {
    "transaction": {
        "messages": [
            {
                "address": "0:852443f8599fe6a5da34fe43049ac4e0beb3071bb2bfb56635ea9421287c283a",
                "amount": "500000000",
                "payload": "",
            }
        ]
    }
}


def _make_client(api_key: str = "test_key") -> MagicMock:
    client = MagicMock()
    client.api_key = api_key
    client.seed = VALID_SEED.split()
    client.wallet_version = "V5R1"
    return client


def _make_wallet(balance_nanotons: int) -> MagicMock:
    wallet = MagicMock()
    wallet.refresh = AsyncMock()
    wallet.balance = balance_nanotons
    wallet.transfer = AsyncMock(return_value=MagicMock(normalized_hash="abc123"))
    return wallet


@pytest.mark.asyncio
async def test_sufficient_balance_broadcasts() -> None:
    # 0.5 TON amount + 0.056 TON gas = 0.556 TON required; wallet has 1 TON
    client = _make_client()
    wallet = _make_wallet(balance_nanotons=1_000_000_000)

    with (
        patch("pyfragment.utils.wallet.TonapiClient") as mock_tonapi,
        patch("pyfragment.utils.wallet.WALLET_CLASSES") as mock_classes,
        patch("pyfragment.utils.wallet.clean_decode", return_value="50 Telegram Stars"),
    ):
        mock_tonapi.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_tonapi.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_classes["V5R1"].from_mnemonic.return_value = (wallet, MagicMock(), None, None)

        result = await process_transaction(client, TRANSACTION_DATA)

    assert result == "abc123"
    wallet.transfer.assert_called_once()


@pytest.mark.asyncio
async def test_insufficient_balance_raises_wallet_error() -> None:
    # wallet has 0.1 TON, needs 0.556 TON
    client = _make_client()
    wallet = _make_wallet(balance_nanotons=100_000_000)

    with (
        patch("pyfragment.utils.wallet.TonapiClient") as mock_tonapi,
        patch("pyfragment.utils.wallet.WALLET_CLASSES") as mock_classes,
    ):
        mock_tonapi.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_tonapi.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_classes["V5R1"].from_mnemonic.return_value = (wallet, MagicMock(), None, None)

        with pytest.raises(WalletError, match="required"):
            await process_transaction(client, TRANSACTION_DATA)

    wallet.transfer.assert_not_called()


@pytest.mark.asyncio
async def test_exactly_minimum_balance_broadcasts() -> None:
    # exactly amount + gas: 500_000_000 + 56_000_000 = 556_000_000 nanotons
    client = _make_client()
    wallet = _make_wallet(balance_nanotons=556_000_000)

    with (
        patch("pyfragment.utils.wallet.TonapiClient") as mock_tonapi,
        patch("pyfragment.utils.wallet.WALLET_CLASSES") as mock_classes,
        patch("pyfragment.utils.wallet.clean_decode", return_value="50 Telegram Stars"),
    ):
        mock_tonapi.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_tonapi.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_classes["V5R1"].from_mnemonic.return_value = (wallet, MagicMock(), None, None)

        result = await process_transaction(client, TRANSACTION_DATA)

    assert result == "abc123"


@pytest.mark.asyncio
async def test_one_nanoton_below_minimum_raises() -> None:
    # 556_000_000 - 1 nanoton: just below threshold
    client = _make_client()
    wallet = _make_wallet(balance_nanotons=555_999_999)

    with (
        patch("pyfragment.utils.wallet.TonapiClient") as mock_tonapi,
        patch("pyfragment.utils.wallet.WALLET_CLASSES") as mock_classes,
    ):
        mock_tonapi.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_tonapi.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_classes["V5R1"].from_mnemonic.return_value = (wallet, MagicMock(), None, None)

        with pytest.raises(WalletError, match="required"):
            await process_transaction(client, TRANSACTION_DATA)


@pytest.mark.asyncio
async def test_invalid_payload_raises_transaction_error() -> None:
    from pyfragment.types import TransactionError

    client = _make_client()
    with pytest.raises(TransactionError):
        await process_transaction(client, {"transaction": {}})
