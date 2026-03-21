"""Unit tests for process_transaction() — balance validation and broadcast retry logic."""

from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from tonutils.exceptions import ProviderResponseError

from pyfragment.types import TransactionError, WalletError
from pyfragment.utils.wallet import process_transaction
from tests.shared import VALID_SEED


def _provider_error(code: int, message: str = "error") -> ProviderResponseError:
    return ProviderResponseError(code=code, message=message, endpoint="api.tonapi.io")


TRANSACTION_DATA = {
    "transaction": {
        "messages": [
            {
                "address": "0:852443f8599fe6a5da34fe43049ac4e0beb3071bb2bfb56635ea9421287c283a",
                "amount": "500000000",  # 0.5 TON
                "payload": "",
            }
        ]
    }
}


def _make_client() -> MagicMock:
    client = MagicMock()
    client.api_key = "test_key"
    client.seed = VALID_SEED.split()
    client.wallet_version = "V5R1"
    return client


def _make_wallet(balance_nanotons: int) -> MagicMock:
    wallet = MagicMock()
    wallet.refresh = AsyncMock()
    wallet.balance = balance_nanotons
    wallet.transfer = AsyncMock(return_value=MagicMock(normalized_hash="abc123"))
    return wallet


@contextmanager
def _patch_wallet(wallet: MagicMock):
    with (
        patch("pyfragment.utils.wallet.TonapiClient") as mock_tonapi,
        patch("pyfragment.utils.wallet.WALLET_CLASSES") as mock_classes,
    ):
        mock_tonapi.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_tonapi.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_classes["V5R1"].from_mnemonic.return_value = (wallet, MagicMock(), None, None)
        yield


# Balance threshold tests


@pytest.mark.asyncio
async def test_sufficient_balance_broadcasts() -> None:
    wallet = _make_wallet(balance_nanotons=1_000_000_000)  # 1 TON, needs 0.556 TON
    with _patch_wallet(wallet), patch("pyfragment.utils.wallet.clean_decode", return_value="50 Telegram Stars"):
        result = await process_transaction(_make_client(), TRANSACTION_DATA)
    assert result == "abc123"
    wallet.transfer.assert_called_once()


@pytest.mark.asyncio
async def test_insufficient_balance_raises() -> None:
    wallet = _make_wallet(balance_nanotons=100_000_000)  # 0.1 TON, needs 0.556 TON
    with _patch_wallet(wallet):
        with pytest.raises(WalletError, match="required"):
            await process_transaction(_make_client(), TRANSACTION_DATA)
    wallet.transfer.assert_not_called()


@pytest.mark.asyncio
async def test_exact_minimum_balance_broadcasts() -> None:
    wallet = _make_wallet(balance_nanotons=556_000_000)  # exactly 0.5 + 0.056 TON
    with _patch_wallet(wallet), patch("pyfragment.utils.wallet.clean_decode", return_value="50 Telegram Stars"):
        result = await process_transaction(_make_client(), TRANSACTION_DATA)
    assert result == "abc123"


@pytest.mark.asyncio
async def test_one_nanoton_below_minimum_raises() -> None:
    wallet = _make_wallet(balance_nanotons=555_999_999)  # 1 nanoton below threshold
    with _patch_wallet(wallet):
        with pytest.raises(WalletError, match="required"):
            await process_transaction(_make_client(), TRANSACTION_DATA)


# Error handling tests


@pytest.mark.asyncio
async def test_invalid_payload_raises() -> None:
    with pytest.raises(TransactionError):
        await process_transaction(_make_client(), {"transaction": {}})


@pytest.mark.asyncio
async def test_balance_check_failed_raises_wallet_error() -> None:
    wallet = _make_wallet(balance_nanotons=1_000_000_000)
    wallet.refresh = AsyncMock(side_effect=RuntimeError("network timeout"))
    with _patch_wallet(wallet):
        with pytest.raises(WalletError, match="balance"):
            await process_transaction(_make_client(), TRANSACTION_DATA)
    wallet.transfer.assert_not_called()


@pytest.mark.asyncio
async def test_rate_limit_retries_and_succeeds() -> None:
    wallet = _make_wallet(balance_nanotons=1_000_000_000)
    wallet.transfer = AsyncMock(side_effect=[_provider_error(429, "rate limited"), MagicMock(normalized_hash="abc123")])
    with _patch_wallet(wallet), patch("pyfragment.utils.wallet.clean_decode", return_value=""):
        result = await process_transaction(_make_client(), TRANSACTION_DATA)
    assert result == "abc123"
    assert wallet.transfer.call_count == 2


@pytest.mark.asyncio
async def test_duplicate_seqno_raises_after_retries() -> None:
    wallet = _make_wallet(balance_nanotons=1_000_000_000)
    err = _provider_error(406, "Duplicate msg_seqno")
    wallet.transfer = AsyncMock(side_effect=[err, err, err])
    with _patch_wallet(wallet), patch("pyfragment.utils.wallet.clean_decode", return_value=""):
        with pytest.raises(TransactionError, match="seqno"):
            await process_transaction(_make_client(), TRANSACTION_DATA)
    assert wallet.transfer.call_count == 3
