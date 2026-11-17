"""Link parameters per flow, need_ton handling, the transfer coordinator and the send retry rules."""

import asyncio
import time
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from tonutils.types import DEFAULT_HTTP_RETRY_POLICY

import pyfragment.domains.payments.flow as _flow_mod
from pyfragment import FragmentClient, LocalTransferCoordinator, SessionExpiredError
from pyfragment.domains.ads.recharge import RECHARGE_FLOW
from pyfragment.domains.ads.topup import TOPUP_FLOW
from pyfragment.domains.giveaways.premium import PREMIUM_GIVEAWAY_FLOW
from pyfragment.domains.giveaways.stars import STARS_GIVEAWAY_FLOW
from pyfragment.domains.payments import PurchaseFlow, run_purchase
from pyfragment.domains.purchases.premium import PREMIUM_FLOW
from pyfragment.domains.purchases.stars import STARS_FLOW
from pyfragment.domains.wallet.transfers import process_transaction
from pyfragment.enums import ApiMethod
from tests.fake_ton import FakeTon, provider_error, use_fake_ton
from tests.shared import (
    FAKE_ACCOUNT,
    FAKE_REQ_ID,
    FAKE_SENT,
    FAKE_TRANSACTION,
    VALID_API_KEY,
    VALID_COOKIES,
    VALID_SEED,
    fixture_json,
)

# Which flows send account/device with get*Link, as fragment.com's frontend does


@pytest.mark.parametrize("flow", [STARS_FLOW, PREMIUM_FLOW, STARS_GIVEAWAY_FLOW, PREMIUM_GIVEAWAY_FLOW])
def test_flows_whose_page_sends_only_the_invoice_id_do_not_send_the_wallet(flow: PurchaseFlow) -> None:
    assert flow.wallet_in_link is False


@pytest.mark.parametrize("flow", [TOPUP_FLOW, RECHARGE_FLOW])
def test_ads_flows_still_send_the_wallet(flow: PurchaseFlow) -> None:
    assert flow.wallet_in_link is True


def make_flow(**options: Any) -> PurchaseFlow:
    return PurchaseFlow(
        page_url="https://fragment.com/stars/buy",
        state_method=ApiMethod.UPDATE_STARS_BUY_STATE,
        init_method=ApiMethod.INIT_BUY_STARS_REQUEST,
        link_method=ApiMethod.GET_BUY_STARS_LINK,
        label="Test purchase",
        **options,
    )


async def link_call_data(client: FragmentClient, flow: PurchaseFlow) -> dict[str, Any]:
    call_mock = AsyncMock(side_effect=[{"req_id": FAKE_REQ_ID, "amount": "0.7"}, FAKE_TRANSACTION])
    with (
        patch.object(client, "call", call_mock),
        patch.object(client.ton_wallet, "account_info", return_value=FAKE_ACCOUNT),
        patch.object(_flow_mod, "process_transaction", AsyncMock(return_value=FAKE_SENT)),
        patch.object(_flow_mod, "confirm_purchase", AsyncMock(return_value=False)),
    ):
        await run_purchase(client, flow, {"recipient": "r"}, {"show_sender": 0})
    link_call = call_mock.call_args_list[1]
    assert link_call.args[0] == flow.link_method
    return dict(link_call.args[1])


@pytest.mark.asyncio
async def test_link_without_wallet_carries_only_id_transaction_and_link_data(client: FragmentClient) -> None:
    data = await link_call_data(client, make_flow(wallet_in_link=False))
    assert data == {"transaction": 1, "id": FAKE_REQ_ID, "show_sender": 0}


@pytest.mark.asyncio
async def test_link_with_wallet_adds_account_and_device(client: FragmentClient) -> None:
    data = await link_call_data(client, make_flow())
    assert set(data) == {"account", "device", "transaction", "id", "show_sender"}


@pytest.mark.asyncio
async def test_need_ton_from_init_is_a_session_error_naming_the_ton_token(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(return_value={"need_ton": True})):
        with pytest.raises(SessionExpiredError, match="stel_ton_token") as excinfo:
            await run_purchase(client, make_flow(), {"recipient": "r"})
    assert "Test purchase" in str(excinfo.value)


# Purchases overlap: only signing and sending is serialized, never the wait for Fragment's confirmation


@pytest.mark.asyncio
async def test_slow_confirmations_of_concurrent_purchases_overlap(client: FragmentClient) -> None:
    async def slow_confirm(*_: Any, **__: Any) -> bool:
        await asyncio.sleep(0.2)
        return True

    call_mock = AsyncMock(
        side_effect=lambda *a, **k: {"req_id": FAKE_REQ_ID} if a[0] == ApiMethod.INIT_BUY_STARS_REQUEST else FAKE_TRANSACTION
    )
    with (
        patch.object(client, "call", call_mock),
        patch.object(client.ton_wallet, "account_info", return_value=FAKE_ACCOUNT),
        patch.object(_flow_mod, "process_transaction", AsyncMock(return_value=FAKE_SENT)),
        patch.object(_flow_mod, "confirm_purchase", slow_confirm),
    ):
        started = time.monotonic()
        results = await asyncio.gather(*(run_purchase(client, make_flow(), {"recipient": "r"}) for _ in range(10)))
        elapsed = time.monotonic() - started

    assert len(results) == 10
    assert elapsed < 1.0  # ten sequential 0.2 s confirmations would take 2 s


# Coordinator


@pytest.mark.asyncio
async def test_local_coordinator_remembers_the_pending_seqno() -> None:
    coordinator = LocalTransferCoordinator()
    assert await coordinator.load_pending() is None
    await coordinator.save_pending(7, 123.0)
    assert await coordinator.load_pending() == (7, 123.0)


@pytest.mark.asyncio
async def test_clients_of_one_wallet_share_the_default_coordinator() -> None:
    with use_fake_ton(FakeTon()):
        async with new_wallet_client() as first, new_wallet_client() as second:
            assert first.ton_wallet.coordinator is second.ton_wallet.coordinator


def new_wallet_client() -> FragmentClient:
    return FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES)


def stars_link() -> dict[str, Any]:
    link = fixture_json("stars_transaction_link_response.json")
    link["transaction"]["validUntil"] = int(time.time()) + 300
    return link


@pytest.mark.asyncio
async def test_expired_pending_seqno_falls_back_to_the_chain() -> None:
    ton = FakeTon(seqno=9)
    with use_fake_ton(ton):
        async with FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES) as client:
            await client.ton_wallet.coordinator.save_pending(3, time.time() - 1)
            params = await client.ton_wallet.transfer_params(int(time.time()) + 60)
    assert params.seqno == 9


@pytest.mark.asyncio
async def test_a_transfer_waits_for_the_pending_one_to_land_before_taking_the_next_seqno() -> None:
    ton = FakeTon(seqno=7)  # message 7 was sent but is not in a block yet

    async def block_arrives(_: float) -> None:
        ton.seqno += 1

    sleep = AsyncMock(side_effect=block_arrives)
    with use_fake_ton(ton), patch("pyfragment.domains.wallet.wallet.asyncio.sleep", sleep):
        async with FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES) as client:
            await client.ton_wallet.coordinator.save_pending(7, time.time() + 60)
            params = await client.ton_wallet.transfer_params(int(time.time()) + 60)
    assert params.seqno == 8
    assert sleep.await_count == 1


@pytest.mark.asyncio
async def test_a_pending_transfer_that_expired_unlanded_no_longer_blocks_the_next_one() -> None:
    ton = FakeTon(seqno=7)
    clock = [time.time()]

    async def tick(_: float) -> None:
        clock[0] += 30

    fake_time = type("FakeTime", (), {"time": staticmethod(lambda: clock[0])})
    with (
        use_fake_ton(ton),
        patch("pyfragment.domains.wallet.wallet.asyncio.sleep", tick),
        patch("pyfragment.domains.wallet.wallet.time", fake_time),
    ):
        async with FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES) as client:
            await client.ton_wallet.coordinator.save_pending(7, clock[0] + 60)
            params = await client.ton_wallet.transfer_params(int(clock[0]) + 120)
    assert params.seqno == 7


@pytest.mark.asyncio
async def test_a_custom_coordinator_is_used_instead_of_the_default() -> None:
    class Spy:
        def __init__(self) -> None:
            self.local = LocalTransferCoordinator()
            self.locked = 0

        def lock(self) -> Any:
            self.locked += 1
            return self.local.lock()

        async def load_pending(self) -> tuple[int, float] | None:
            return await self.local.load_pending()

        async def save_pending(self, seqno: int, valid_until: float) -> None:
            await self.local.save_pending(seqno, valid_until)

    spy = Spy()
    ton = FakeTon()
    with use_fake_ton(ton):
        async with FragmentClient(
            seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES, transfer_coordinator=spy
        ) as client:
            await process_transaction(client, stars_link())
    assert spy.locked == 1
    assert await spy.load_pending() is not None


# The provider client retries rate limits and transient errors itself


@pytest.mark.parametrize(("provider", "client_class"), [("tonapi", "TonapiClient"), ("toncenter", "ToncenterClient")])
def test_provider_clients_are_built_with_tonutils_retry_policy(provider: str, client_class: str) -> None:
    from pyfragment.domains.wallet.wallet import make_ton_client

    client = FragmentClient(api_provider=provider, seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES)
    with patch(f"pyfragment.domains.wallet.wallet.{client_class}") as provider_client:
        make_ton_client(client)
    assert provider_client.call_args.kwargs["retry_policy"] is DEFAULT_HTTP_RETRY_POLICY


@pytest.mark.asyncio
async def test_a_rate_limited_send_is_logged_not_raised() -> None:
    ton = FakeTon()
    ton.send_errors = [(provider_error(429), False)]
    with use_fake_ton(ton):
        async with FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES) as client:
            await process_transaction(client, stars_link())
    assert len(ton.sent) == 1
    assert ton.landed == []


# Session and wallet management calls surface Fragment's error text


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["logout", "link_wallet", "disconnect_wallet"])
async def test_session_calls_raise_on_an_error_body(client: FragmentClient, method: str) -> None:
    from pyfragment import FragmentAPIError

    with patch.object(client, "call", AsyncMock(return_value={"error": "nope"})):
        with pytest.raises(FragmentAPIError, match="nope"):
            await getattr(client, method)()


@pytest.mark.asyncio
async def test_check_premium_recipient_rejects_unknown_months(client: FragmentClient) -> None:
    from pyfragment import ConfigurationError

    with pytest.raises(ConfigurationError):
        await client.check_premium_recipient("@user", months=5)
