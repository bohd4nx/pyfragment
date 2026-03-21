"""Unit tests for number methods — get_login_code, toggle_login_codes, terminate_sessions."""

from unittest.mock import AsyncMock, patch

import pytest

from pyfragment import AnonymousNumberError, FragmentClient, LoginCodeResult, TerminateSessionsResult
from tests.shared import FAKE_HASH

FAKE_HTML_WITH_CODE = """
<table>
  <tr>
    <td class="table-cell-value">12345</td>
  </tr>
  <tr>
    <td>session data</td>
  </tr>
</table>
"""

FAKE_HTML_NO_CODE = "<table><tr><td>no code here</td></tr></table>"

FAKE_TERMINATE_HASH = "terminate_hash_abc123"


# get_login_code tests


@pytest.mark.asyncio
async def test_get_login_code_returns_code(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.anonymous_number.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch(
            "pyfragment.methods.anonymous_number.fragment_request",
            AsyncMock(return_value={"html": FAKE_HTML_WITH_CODE}),
        ),
    ):
        result = await client.get_login_code("+1234567890")

    assert isinstance(result, LoginCodeResult)
    assert result.number == "+1234567890"
    assert result.code == "12345"
    assert result.active_sessions == 2  # 2 <tr> in the HTML


@pytest.mark.asyncio
async def test_get_login_code_no_pending_code(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.anonymous_number.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch(
            "pyfragment.methods.anonymous_number.fragment_request",
            AsyncMock(return_value={"html": FAKE_HTML_NO_CODE}),
        ),
    ):
        result = await client.get_login_code("1234567890")

    assert result.code is None
    assert result.active_sessions == 1


@pytest.mark.asyncio
async def test_get_login_code_no_html_returns_none(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.anonymous_number.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.methods.anonymous_number.fragment_request", AsyncMock(return_value={})),
    ):
        result = await client.get_login_code("+1234567890")

    assert result.code is None
    assert result.active_sessions == 0


# terminate_sessions tests


@pytest.mark.asyncio
async def test_terminate_sessions_success(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.anonymous_number.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch(
            "pyfragment.methods.anonymous_number.fragment_request",
            AsyncMock(
                side_effect=[
                    {"terminate_hash": FAKE_TERMINATE_HASH},  # step 1: confirmation
                    {"msg": "All sessions terminated"},  # step 2: confirmed
                ]
            ),
        ),
    ):
        result = await client.terminate_sessions("+1234567890")

    assert isinstance(result, TerminateSessionsResult)
    assert result.number == "+1234567890"
    assert result.message == "All sessions terminated"


@pytest.mark.asyncio
async def test_terminate_sessions_not_owned_raises(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.anonymous_number.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.methods.anonymous_number.fragment_request", AsyncMock(return_value={})),
    ):
        with pytest.raises(AnonymousNumberError, match="not associated"):
            await client.terminate_sessions("+1234567890")


@pytest.mark.asyncio
async def test_terminate_sessions_api_error_raises(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.anonymous_number.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch(
            "pyfragment.methods.anonymous_number.fragment_request",
            AsyncMock(return_value={"error": "SESSION_ALREADY_TERMINATED"}),
        ),
    ):
        with pytest.raises(AnonymousNumberError, match="SESSION_ALREADY_TERMINATED"):
            await client.terminate_sessions("+1234567890")


@pytest.mark.asyncio
async def test_terminate_sessions_confirm_error_raises(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.anonymous_number.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch(
            "pyfragment.methods.anonymous_number.fragment_request",
            AsyncMock(
                side_effect=[
                    {"terminate_hash": FAKE_TERMINATE_HASH},
                    {"error": "INTERNAL_ERROR"},
                ]
            ),
        ),
    ):
        with pytest.raises(AnonymousNumberError, match="INTERNAL_ERROR"):
            await client.terminate_sessions("+1234567890")


# toggle_login_codes tests


@pytest.mark.asyncio
async def test_toggle_login_codes_enable(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.anonymous_number.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.methods.anonymous_number.fragment_request", AsyncMock(return_value={"ok": True})) as mock_req,
    ):
        await client.toggle_login_codes("+1234567890", can_receive=True)

    call_data = mock_req.call_args[0][3]
    assert call_data["can_receive"] == 1
    assert call_data["method"] == "toggleLoginCodes"


@pytest.mark.asyncio
async def test_toggle_login_codes_disable(client: FragmentClient) -> None:
    with (
        patch("pyfragment.methods.anonymous_number.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.methods.anonymous_number.fragment_request", AsyncMock(return_value={"ok": True})) as mock_req,
    ):
        await client.toggle_login_codes("+1234567890", can_receive=False)

    call_data = mock_req.call_args[0][3]
    assert call_data["can_receive"] == 0


# strip_plus tests


@pytest.mark.asyncio
async def test_get_login_code_strips_plus(client: FragmentClient) -> None:
    """Number passed with '+' is stripped before the API call."""
    with (
        patch("pyfragment.methods.anonymous_number.get_fragment_hash", AsyncMock(return_value=FAKE_HASH)),
        patch("pyfragment.methods.anonymous_number.fragment_request", AsyncMock(return_value={})) as mock_req,
    ):
        await client.get_login_code("+1234567890")

    call_data = mock_req.call_args[0][3]
    assert call_data["number"] == "1234567890"
