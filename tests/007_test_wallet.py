"""Verify wallet inspection returns exact GRAM (ex TON) and USDT balances, and the wallet's connection lifecycle."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from ton_core import ContractState
from tonutils.exceptions import ProviderResponseError, RunGetMethodError

from pyfragment import ChainError, FragmentClient, ProviderError, WalletInfo
from pyfragment.constants import TVM_EXIT_ACCOUNT_NOT_FOUND
from pyfragment.domains.wallet.balance import get_usdt_balance
from tests.fake_ton import FakeTon, use_fake_ton
from tests.shared import VALID_API_KEY, VALID_COOKIES, VALID_SEED

# get_wallet()


@pytest.mark.asyncio
async def test_get_wallet_returns_exact_balances(client: FragmentClient) -> None:
    with (
        use_fake_ton(FakeTon(balance=1_500_000_001)),
        patch("pyfragment.domains.wallet.balance.get_usdt_balance", AsyncMock(return_value=12_345_678)),
    ):
        result = await client.get_wallet()

    assert isinstance(result, WalletInfo)
    assert result.address == client.ton_wallet.wallet().address.to_str(is_user_friendly=True, is_bounceable=False)
    assert result.state == "active"
    assert result.gram_balance == Decimal("1.500000001")  # not rounded to 4 places any more
    assert result.usdt_balance == Decimal("12.345678")


@pytest.mark.asyncio
async def test_get_wallet_of_an_empty_undeployed_wallet(client: FragmentClient) -> None:
    with (
        use_fake_ton(FakeTon(balance=0, state=ContractState.UNINIT)),
        patch("pyfragment.domains.wallet.balance.get_usdt_balance", AsyncMock(return_value=0)),
    ):
        result = await client.get_wallet()

    assert result.gram_balance == 0 and result.usdt_balance == 0
    assert result.state == "uninit"


@pytest.mark.asyncio
async def test_get_wallet_usdt_failure_reports_unknown(client: FragmentClient) -> None:
    usdt_down = AsyncMock(side_effect=ProviderError("boom"))
    with use_fake_ton(FakeTon(balance=2_000_000_000)), patch("pyfragment.domains.wallet.balance.get_usdt_balance", usdt_down):
        result = await client.get_wallet()

    assert result.gram_balance == Decimal(2)
    assert result.usdt_balance is None


@pytest.mark.asyncio
async def test_get_wallet_provider_failure_raises_instead_of_reporting_an_empty_wallet(client: FragmentClient) -> None:
    # tonutils' wallet.refresh() turns a bad API key or an outage into "nonexistent, zero balance";
    # get_wallet must surface the failure instead.
    ton = FakeTon()
    ton.info_errors = [RuntimeError("401 invalid token")]
    with use_fake_ton(ton):
        with pytest.raises(ProviderError, match="401 invalid token") as exc_info:
            await client.get_wallet()
    assert isinstance(exc_info.value, ChainError) and exc_info.value.retryable


# make_ton_client — provider selection


def test_make_ton_client_uses_toncenter_for_toncenter_provider(client: FragmentClient) -> None:
    from tonutils.clients import ToncenterClient

    from pyfragment.domains.wallet.wallet import make_ton_client
    from pyfragment.enums import ApiProvider

    client.api_provider = ApiProvider.TONCENTER
    assert isinstance(make_ton_client(client), ToncenterClient)


def test_make_ton_client_uses_tonapi_for_tonapi_provider(client: FragmentClient) -> None:
    from tonutils.clients import TonapiClient

    from pyfragment.domains.wallet.wallet import make_ton_client
    from pyfragment.enums import ApiProvider

    client.api_provider = ApiProvider.TONAPI
    assert isinstance(make_ton_client(client), TonapiClient)


# One connection per client


@pytest.mark.asyncio
async def test_connection_is_reused_and_closed_with_the_client() -> None:
    ton = FakeTon()
    with (
        patch("pyfragment.domains.wallet.wallet.make_ton_client", return_value=ton) as make_ton_client,
        patch("pyfragment.domains.wallet.balance.get_usdt_balance", AsyncMock(return_value=0)),
    ):
        async with FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES) as client:
            await client.get_wallet()
            await client.get_wallet()
            assert ton.connected
    assert make_ton_client.call_count == 1
    assert ton.closed and not ton.connected


@pytest.mark.asyncio
async def test_account_info_needs_no_network(client: FragmentClient) -> None:
    ton = FakeTon()
    with use_fake_ton(ton):
        account = client.ton_wallet.account_info()
        assert client.ton_wallet.account_info() is account
    assert not ton.connected
    wallet = client.ton_wallet.wallet()
    assert account["address"] == wallet.address.to_str(False, False)
    assert account["chain"] == "-239"


# get_usdt_balance — error paths


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [
        # tonapi answers 404 for an owner without a USDT jetton wallet ...
        ProviderResponseError(code=404, message="not found", endpoint="tonapi.io"),
        # ... toncenter a TVM exit code -13 (the jetton wallet isn't deployed).
        RunGetMethodError(address="0:abc", exit_code=TVM_EXIT_ACCOUNT_NOT_FOUND, method_name="get_wallet_data"),
    ],
)
async def test_get_usdt_balance_missing_jetton_wallet_is_zero(error: Exception) -> None:
    with patch("pyfragment.domains.wallet.balance.get_wallet_address_get_method", AsyncMock(side_effect=error)):
        assert await get_usdt_balance(MagicMock(), "0:abc") == 0


@pytest.mark.asyncio
async def test_get_usdt_balance_reads_units() -> None:
    with (
        patch("pyfragment.domains.wallet.balance.get_wallet_address_get_method", AsyncMock(return_value="0:def")),
        patch("pyfragment.domains.wallet.balance.get_wallet_data_get_method", AsyncMock(return_value=[1_234_567])),
    ):
        assert await get_usdt_balance(MagicMock(), "0:abc") == 1_234_567


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [
        RunGetMethodError(address="0:abc", exit_code=11, method_name="get_wallet_data"),
        ProviderResponseError(code=401, message="unauthorized", endpoint="api.tonapi.io"),
        RuntimeError("timeout"),
    ],
)
async def test_get_usdt_balance_failure_raises_provider_error(error: Exception) -> None:
    with patch("pyfragment.domains.wallet.balance.get_wallet_address_get_method", AsyncMock(side_effect=error)):
        with pytest.raises(ProviderError, match="USDT"):
            await get_usdt_balance(MagicMock(), "0:abc")


def test_wallet_repr_uses_fixed_point_for_small_balances() -> None:
    info = WalletInfo(
        address="UQCtest",
        state="active",
        gram_balance=Decimal("0.000000001"),
        usdt_balance=Decimal("0"),
    )
    r = repr(info)
    assert "E" not in r and "0.000000001" in r


def test_wallet_repr_unknown_usdt() -> None:
    info = WalletInfo(address="UQCtest", state="uninit", gram_balance=Decimal("0"), usdt_balance=None)
    assert "unknown" in repr(info)
