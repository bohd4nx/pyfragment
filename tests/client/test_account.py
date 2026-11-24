"""Account methods of the client: logout, wallet linking, disconnecting and reading the wallet."""

from decimal import Decimal

import pytest

from pyfragment import FragmentAPIError, FragmentClient, SessionExpiredError, WalletAlreadyLinkedError
from pyfragment.constants.fragment import FRAGMENT_BASE_URL, PROFILE_PAGE
from pyfragment.enums import ApiError
from tests.support.fake_fragment import FakeFragment
from tests.support.fake_ton import FakeTon

ACCOUNT_CALLS = [
    ("logout", "logOut", FRAGMENT_BASE_URL),
    ("link_wallet", "linkWallet", PROFILE_PAGE),
    ("disconnect_wallet", "tonLogOut", FRAGMENT_BASE_URL),
]


@pytest.mark.parametrize(("name", "method", "page"), ACCOUNT_CALLS)
class TestSessionCalls:
    async def test_sends_its_method_from_its_page(
        self, client: FragmentClient, fragment: FakeFragment, name: str, method: str, page: str
    ) -> None:
        fragment.reply(method, {"ok": True})

        assert await getattr(client, name)() is None

        (call,) = fragment.calls
        assert (call.method, call.page_url) == (method, page)

    async def test_an_error_body_surfaces_fragment_s_text(
        self, client: FragmentClient, fragment: FakeFragment, name: str, method: str, page: str
    ) -> None:
        fragment.reply(method, {"error": "nope"})

        with pytest.raises(FragmentAPIError, match="nope"):
            await getattr(client, name)()

    async def test_a_denied_session_is_reported_as_expired(
        self, client: FragmentClient, fragment: FakeFragment, name: str, method: str, page: str
    ) -> None:
        fragment.reply(method, SessionExpiredError(SessionExpiredError.ACCESS_DENIED.format(context=method)))

        with pytest.raises(SessionExpiredError):
            await getattr(client, name)()


class TestLinkWallet:
    async def test_a_wallet_that_is_already_linked_has_its_own_error(
        self, client: FragmentClient, fragment: FakeFragment
    ) -> None:
        fragment.reply("linkWallet", {"error": f"This wallet is {ApiError.WALLET_ALREADY_LINKED} to an account."})

        with pytest.raises(WalletAlreadyLinkedError, match=WalletAlreadyLinkedError.LINKED):
            await client.link_wallet()

    def test_it_is_a_fragment_api_error(self) -> None:
        assert issubclass(WalletAlreadyLinkedError, FragmentAPIError)


class TestGetWallet:
    async def test_reports_the_funded_wallet(self, client: FragmentClient, fake_ton: FakeTon) -> None:
        info = await client.get_wallet()

        assert info.gram_balance == Decimal(10)
        assert info.state == fake_ton.state.value
