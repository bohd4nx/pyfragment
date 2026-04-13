"""Unit tests for anonymous number methods — login codes and session management."""

from unittest.mock import AsyncMock, patch

import pytest

from pyfragment import AnonymousNumberError, FragmentClient, LoginCodeResult, TerminateSessionsResult
from tests.shared import FAKE_HTML_NO_CODE, FAKE_HTML_WITH_CODE, FAKE_TERMINATE_HASH

# get_login_code mocked tests


@pytest.mark.asyncio
async def test_get_login_code_returns_code(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(return_value={"html": FAKE_HTML_WITH_CODE})):
        result = await client.get_login_code("+1234567890")

    assert isinstance(result, LoginCodeResult)
    assert result.number == "+1234567890"
    assert result.code == "12345"
    assert result.active_sessions == 2  # 2 <tr> in the HTML


@pytest.mark.asyncio
async def test_get_login_code_no_pending_code(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(return_value={"html": FAKE_HTML_NO_CODE})):
        result = await client.get_login_code("1234567890")

    assert result.code is None
    assert result.active_sessions == 1


@pytest.mark.asyncio
async def test_get_login_code_no_html_returns_none(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(return_value={})):
        result = await client.get_login_code("+1234567890")

    assert result.code is None
    assert result.active_sessions == 0


# terminate_sessions mocked tests


@pytest.mark.asyncio
async def test_terminate_sessions_success(client: FragmentClient) -> None:
    with patch.object(
        client,
        "call",
        AsyncMock(
            side_effect=[
                {"terminate_hash": FAKE_TERMINATE_HASH},  # step 1: confirmation
                {"msg": "All sessions terminated"},  # step 2: confirmed
            ]
        ),
    ):
        result = await client.terminate_sessions("+1234567890")

    assert isinstance(result, TerminateSessionsResult)
    assert result.number == "+1234567890"
    assert result.message == "All sessions terminated"


@pytest.mark.asyncio
async def test_terminate_sessions_not_owned_raises(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(return_value={})):
        with pytest.raises(AnonymousNumberError, match="not associated"):
            await client.terminate_sessions("+1234567890")


@pytest.mark.asyncio
async def test_terminate_sessions_api_error_raises(client: FragmentClient) -> None:
    with patch.object(client, "call", AsyncMock(return_value={"error": "SESSION_ALREADY_TERMINATED"})):
        with pytest.raises(AnonymousNumberError, match="SESSION_ALREADY_TERMINATED"):
            await client.terminate_sessions("+1234567890")


@pytest.mark.asyncio
async def test_terminate_sessions_confirm_error_raises(client: FragmentClient) -> None:
    with patch.object(
        client,
        "call",
        AsyncMock(
            side_effect=[
                {"terminate_hash": FAKE_TERMINATE_HASH},
                {"error": "INTERNAL_ERROR"},
            ]
        ),
    ):
        with pytest.raises(AnonymousNumberError, match="INTERNAL_ERROR"):
            await client.terminate_sessions("+1234567890")


# toggle_login_codes mocked tests


@pytest.mark.asyncio
async def test_toggle_login_codes_enable(client: FragmentClient) -> None:
    mock_call = AsyncMock(return_value={"ok": True})
    with patch.object(client, "call", mock_call):
        await client.toggle_login_codes("+1234567890", can_receive=True)

    call_data = mock_call.call_args[0][1]
    assert call_data["can_receive"] == 1


@pytest.mark.asyncio
async def test_toggle_login_codes_disable(client: FragmentClient) -> None:
    mock_call = AsyncMock(return_value={"ok": True})
    with patch.object(client, "call", mock_call):
        await client.toggle_login_codes("+1234567890", can_receive=False)

    call_data = mock_call.call_args[0][1]
    assert call_data["can_receive"] == 0


# strip_plus mocked tests


@pytest.mark.asyncio
async def test_get_login_code_strips_plus(client: FragmentClient) -> None:
    """Number passed with '+' is stripped before the API call."""
    mock_call = AsyncMock(return_value={})
    with patch.object(client, "call", mock_call):
        await client.get_login_code("+1234567890")

    call_data = mock_call.call_args[0][1]
    assert call_data["number"] == "1234567890"
