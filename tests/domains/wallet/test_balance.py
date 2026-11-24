"""get_wallet and the USDT balance lookup."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from ton_core import ContractState
from tonutils.exceptions import ProviderResponseError, RunGetMethodError

from pyfragment import ChainError, FragmentClient, ProviderError, WalletInfo
from pyfragment.constants.chain import TVM_EXIT_ACCOUNT_NOT_FOUND
from pyfragment.domains.wallet.balance import get_usdt_balance, is_missing_jetton_wallet
from tests.support.fake_ton import FakeTon

BALANCE = "pyfragment.domains.wallet.balance"


class TestGetWallet:
    async def test_returns_exact_balances(
        self, fake_ton: FakeTon, client: FragmentClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake_ton.balance = 1_500_000_001
        monkeypatch.setattr(f"{BALANCE}.get_usdt_balance", AsyncMock(return_value=12_345_678))

        result = await client.get_wallet()

        assert isinstance(result, WalletInfo)
        assert result.address == client.ton_wallet.wallet().address.to_str(is_user_friendly=True, is_bounceable=False)
        assert result.state == "active"
        assert result.gram_balance == Decimal("1.500000001")
        assert result.usdt_balance == Decimal("12.345678")

    async def test_empty_undeployed_wallet(
        self, fake_ton: FakeTon, client: FragmentClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake_ton.balance, fake_ton.state = 0, ContractState.UNINIT
        monkeypatch.setattr(f"{BALANCE}.get_usdt_balance", AsyncMock(return_value=0))

        result = await client.get_wallet()

        assert result.gram_balance == 0 and result.usdt_balance == 0
        assert result.state == "uninit"

    async def test_failed_usdt_lookup_reports_unknown_not_zero(
        self, fake_ton: FakeTon, client: FragmentClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake_ton.balance = 2_000_000_000
        monkeypatch.setattr(f"{BALANCE}.get_usdt_balance", AsyncMock(side_effect=ProviderError("boom")))

        result = await client.get_wallet()

        assert result.gram_balance == Decimal(2)
        assert result.usdt_balance is None

    async def test_provider_failure_raises_instead_of_reporting_an_empty_wallet(
        self, fake_ton: FakeTon, client: FragmentClient
    ) -> None:
        # tonutils' wallet.refresh() would turn a bad API key or an outage into "nonexistent, zero balance".
        fake_ton.info_errors = [RuntimeError("401 invalid token")]
        with pytest.raises(ProviderError, match="401 invalid token") as exc_info:
            await client.get_wallet()
        assert isinstance(exc_info.value, ChainError) and exc_info.value.retryable


class TestGetUsdtBalance:
    async def test_reads_the_units_of_the_jetton_wallet(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(f"{BALANCE}.get_wallet_address_get_method", AsyncMock(return_value="0:def"))
        monkeypatch.setattr(f"{BALANCE}.get_wallet_data_get_method", AsyncMock(return_value=[1_234_567]))
        assert await get_usdt_balance(MagicMock(), "0:abc") == 1_234_567

    async def test_empty_wallet_data_is_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(f"{BALANCE}.get_wallet_address_get_method", AsyncMock(return_value="0:def"))
        monkeypatch.setattr(f"{BALANCE}.get_wallet_data_get_method", AsyncMock(return_value=[]))
        assert await get_usdt_balance(MagicMock(), "0:abc") == 0

    @pytest.mark.parametrize(
        "error",
        [
            ProviderResponseError(code=404, message="not found", endpoint="tonapi.io"),
            RunGetMethodError(address="0:abc", exit_code=TVM_EXIT_ACCOUNT_NOT_FOUND, method_name="get_wallet_data"),
        ],
        ids=["tonapi-404", "toncenter-exit-13"],
    )
    async def test_missing_jetton_wallet_is_zero(self, monkeypatch: pytest.MonkeyPatch, error: Exception) -> None:
        monkeypatch.setattr(f"{BALANCE}.get_wallet_address_get_method", AsyncMock(side_effect=error))
        assert is_missing_jetton_wallet(error)
        assert await get_usdt_balance(MagicMock(), "0:abc") == 0

    @pytest.mark.parametrize(
        "error",
        [
            RunGetMethodError(address="0:abc", exit_code=11, method_name="get_wallet_data"),
            ProviderResponseError(code=401, message="unauthorized", endpoint="api.tonapi.io"),
            RuntimeError("timeout"),
        ],
        ids=["other-exit-code", "unauthorized", "network"],
    )
    async def test_any_other_failure_is_a_provider_error(self, monkeypatch: pytest.MonkeyPatch, error: Exception) -> None:
        monkeypatch.setattr(f"{BALANCE}.get_wallet_address_get_method", AsyncMock(side_effect=error))
        assert not is_missing_jetton_wallet(error)
        with pytest.raises(ProviderError, match="USDT"):
            await get_usdt_balance(MagicMock(), "0:abc")

    async def test_provider_status_is_kept_on_the_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        error = ProviderResponseError(code=401, message="unauthorized", endpoint="api.tonapi.io")
        monkeypatch.setattr(f"{BALANCE}.get_wallet_address_get_method", AsyncMock(side_effect=error))
        with pytest.raises(ProviderError) as exc_info:
            await get_usdt_balance(MagicMock(), "0:abc")
        assert exc_info.value.status == 401 and not exc_info.value.retryable
