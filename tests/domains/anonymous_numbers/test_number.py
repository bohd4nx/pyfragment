"""Login codes and sessions of an anonymous number."""

import pytest

from pyfragment import AnonymousNumberError, FragmentClient, LoginCodeResult, TerminateSessionsResult
from pyfragment.constants.fragment import NUMBERS_PAGE
from pyfragment.enums import ApiMethod
from tests.support.fake_fragment import FakeFragment

HASH = "terminate_hash_abc123"
CODE_HTML = '<table><tr><td class="table-cell-value">12345</td></tr><tr><td>session</td></tr></table>'


class TestGetLoginCode:
    async def test_code_and_sessions(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(ApiMethod.UPDATE_LOGIN_CODES, {"html": CODE_HTML})

        result = await client.get_login_code("+88801234567")

        assert result == LoginCodeResult(number="+88801234567", code="12345", active_sessions=2)

    async def test_leading_plus_is_stripped_from_the_request_only(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(ApiMethod.UPDATE_LOGIN_CODES, {})

        result = await client.get_login_code("+88801234567")

        assert fragment.calls[0].data == {"number": "88801234567", "lt": "0", "from_app": "1"}
        assert fragment.calls[0].page_url == NUMBERS_PAGE
        assert result.number == "+88801234567"

    @pytest.mark.parametrize("response", [{}, {"html": None}, {"html": False}, {"html": ""}])
    async def test_no_html_means_no_code_and_no_sessions(
        self, client: FragmentClient, fragment: FakeFragment, response: dict[str, object]
    ) -> None:
        fragment.reply(ApiMethod.UPDATE_LOGIN_CODES, response)

        result = await client.get_login_code("88801234567")

        assert (result.code, result.active_sessions) == (None, 0)


class TestToggleLoginCodes:
    @pytest.mark.parametrize(("can_receive", "sent"), [(True, 1), (False, 0)])
    async def test_flag_is_sent_as_an_int(
        self, client: FragmentClient, fragment: FakeFragment, can_receive: bool, sent: int
    ) -> None:
        fragment.reply(ApiMethod.TOGGLE_LOGIN_CODES, {"ok": True})

        await client.toggle_login_codes("+88801234567", can_receive=can_receive)

        assert fragment.calls[0].data == {"number": "88801234567", "can_receive": sent}
        assert fragment.calls[0].page_url == NUMBERS_PAGE

    async def test_error_is_an_anonymous_number_error(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(ApiMethod.TOGGLE_LOGIN_CODES, {"error": "Number not found"})

        with pytest.raises(AnonymousNumberError, match=r"toggle login codes for '\+88801234567'.*Number not found"):
            await client.toggle_login_codes("+88801234567", can_receive=True)


class TestTerminateSessions:
    async def test_two_steps_the_second_confirms_with_the_hash(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(ApiMethod.TERMINATE_PHONE_SESSIONS, {"terminate_hash": HASH}, {"msg": "All sessions terminated"})

        result = await client.terminate_sessions("+88801234567")

        assert result == TerminateSessionsResult(number="+88801234567", message="All sessions terminated")
        assert [call.data for call in fragment.calls] == [
            {"number": "88801234567"},
            {"number": "88801234567", "terminate_hash": HASH},
        ]
        assert {call.page_url for call in fragment.calls} == {NUMBERS_PAGE}

    async def test_confirmation_without_a_message(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(ApiMethod.TERMINATE_PHONE_SESSIONS, {"terminate_hash": HASH}, {"ok": True})

        assert (await client.terminate_sessions("88801234567")).message is None

    async def test_no_hash_means_the_number_is_not_the_accounts(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(ApiMethod.TERMINATE_PHONE_SESSIONS, {})

        with pytest.raises(AnonymousNumberError, match="not associated with your Fragment account"):
            await client.terminate_sessions("+88801234567")

        assert len(fragment.calls) == 1

    async def test_error_on_the_first_step(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(ApiMethod.TERMINATE_PHONE_SESSIONS, {"error": "SESSION_ALREADY_TERMINATED"})

        with pytest.raises(AnonymousNumberError, match="SESSION_ALREADY_TERMINATED"):
            await client.terminate_sessions("+88801234567")

        assert len(fragment.calls) == 1

    async def test_error_on_the_confirmation(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(ApiMethod.TERMINATE_PHONE_SESSIONS, {"terminate_hash": HASH}, {"error": "INTERNAL_ERROR"})

        with pytest.raises(AnonymousNumberError, match=r"terminate sessions for '\+88801234567'.*INTERNAL_ERROR"):
            await client.terminate_sessions("+88801234567")


class TestLoginCodeErrors:
    async def test_fragment_error_raises(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(ApiMethod.UPDATE_LOGIN_CODES, {"error": "Access denied"})

        with pytest.raises(AnonymousNumberError, match="88801234567"):
            await client.get_login_code("+88801234567")
