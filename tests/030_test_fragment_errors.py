"""Fragment's error answers (texts captured from fragment.com) become typed errors, and nothing is signed after one."""

from unittest.mock import AsyncMock, patch

import pytest

import pyfragment.domains.payments.flow as _flow_mod
from pyfragment import (
    AboveMaximumError,
    ChannelNotFoundError,
    FragmentAPIError,
    FragmentClient,
    InvalidPackageError,
    InvoiceExpiredError,
    WalletAlreadyLinkedError,
)
from tests.shared import FAKE_ACCOUNT, FAKE_RECIPIENT, FAKE_REQ_ID, FAKE_SENT, FAKE_TRANSACTION

CHANNEL_FOUND = {"found": {"recipient": FAKE_RECIPIENT}}


def sign_mock() -> AsyncMock:
    return AsyncMock(return_value=FAKE_SENT)


# A purchase's get*Link answers with an error: nothing is signed


@pytest.mark.asyncio
async def test_expired_invoice_is_a_retryable_error_and_nothing_is_signed(client: FragmentClient) -> None:
    call_mock = AsyncMock(side_effect=[CHANNEL_FOUND, {}, {"req_id": FAKE_REQ_ID}, {"error": "Session expired"}])
    signing = sign_mock()
    with (
        patch.object(client, "call", call_mock),
        patch.object(_flow_mod, "process_transaction", signing),
        pytest.raises(InvoiceExpiredError) as exc_info,
    ):
        await client.purchase_stars("@user", amount=500)

    assert exc_info.value.retryable
    assert "Stars purchase" in str(exc_info.value)
    signing.assert_not_awaited()


@pytest.mark.asyncio
async def test_any_other_link_error_is_raised_instead_of_an_invalid_payload(client: FragmentClient) -> None:
    call_mock = AsyncMock(side_effect=[CHANNEL_FOUND, {}, {"req_id": FAKE_REQ_ID}, {"error": "Something new"}])
    signing = sign_mock()
    with (
        patch.object(client, "call", call_mock),
        patch.object(_flow_mod, "process_transaction", signing),
        pytest.raises(FragmentAPIError, match="Something new"),
    ):
        await client.purchase_stars("@user", amount=500)

    signing.assert_not_awaited()


# Giveaway price calls report what Fragment refuses before an invoice is opened


@pytest.mark.asyncio
async def test_stars_giveaway_package_Fragment_does_not_sell_is_an_invalid_package_error(client: FragmentClient) -> None:
    call_mock = AsyncMock(
        side_effect=[CHANNEL_FOUND, {}, {"error": "Please select one of the star packages."}],
    )
    with patch.object(client, "call", call_mock), pytest.raises(InvalidPackageError):
        await client.giveaway_stars("@channel", winners=1, amount=501)

    assert call_mock.await_count == 3  # no invoice was requested


@pytest.mark.asyncio
async def test_premium_giveaway_over_the_subscription_limit_reports_the_maximum(client: FragmentClient) -> None:
    call_mock = AsyncMock(
        side_effect=[CHANNEL_FOUND, {}, {"ok": True, "error": "You can choose up to 24000 subscriptions"}],
    )
    with patch.object(client, "call", call_mock), pytest.raises(AboveMaximumError) as exc_info:
        await client.giveaway_premium("@channel", winners=24_000, months=3)

    assert exc_info.value.maximum == 24_000
    assert call_mock.await_count == 3


@pytest.mark.asyncio
async def test_stars_giveaway_prices_are_requested_with_the_package_and_winners(client: FragmentClient) -> None:
    call_mock = AsyncMock(side_effect=[CHANNEL_FOUND, {}, {"ok": True}, {"req_id": FAKE_REQ_ID}, FAKE_TRANSACTION])
    with (
        patch.object(client, "call", call_mock),
        patch.object(client.ton_wallet, "account_info", return_value=FAKE_ACCOUNT),
        patch.object(_flow_mod, "process_transaction", sign_mock()),
    ):
        await client.giveaway_stars("@channel", winners=10, amount=1_000)

    assert call_mock.await_args_list[2].args[1] == {"quantity": 10, "stars": 1_000}


# A user, bot or unknown name where a channel is wanted


@pytest.mark.asyncio
@pytest.mark.parametrize("giveaway", ["giveaway_stars", "giveaway_premium"])
async def test_giveaway_for_a_user_is_a_channel_not_found_error(client: FragmentClient, giveaway: str) -> None:
    args = {"giveaway_stars": {"amount": 500}, "giveaway_premium": {"months": 3}}[giveaway]
    answer = {"error": "Please enter a username assigned to a channel."}
    with patch.object(client, "call", AsyncMock(return_value=answer)), pytest.raises(ChannelNotFoundError) as exc_info:
        await getattr(client, giveaway)("@someone", winners=1, **args)

    assert "@someone" in str(exc_info.value)
    assert "does not belong to a channel" in str(exc_info.value)


# link_wallet


@pytest.mark.asyncio
async def test_link_wallet_reports_an_already_linked_wallet(client: FragmentClient) -> None:
    answer = {"error": "This wallet is already linked to an account."}
    with patch.object(client, "call", AsyncMock(return_value=answer)), pytest.raises(WalletAlreadyLinkedError):
        await client.link_wallet()
