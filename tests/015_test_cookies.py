"""Unit tests for get_cookies_from_browser() — browser cookie extraction helper."""

from unittest.mock import MagicMock, patch

import pytest

from pyfragment import get_cookies_from_browser
from pyfragment.types import CookieError
from pyfragment.types.constants import REQUIRED_COOKIE_KEYS

FAKE_JAR = [
    {"name": "stel_ssid", "value": "abc123", "domain": "fragment.com"},
    {"name": "stel_dt", "value": "-120", "domain": "fragment.com"},
    {"name": "stel_token", "value": "tok_xyz", "domain": "fragment.com"},
    {"name": "stel_ton_token", "value": "ton_xyz", "domain": "fragment.com"},
    {"name": "unrelated", "value": "noise", "domain": "fragment.com"},
]


def _mock_rookiepy(jar: list[dict] | None = None) -> MagicMock:
    mock = MagicMock()
    mock.chrome.return_value = jar if jar is not None else FAKE_JAR
    return mock


# unsupported browser tests


def test_unsupported_browser_raises() -> None:
    with pytest.raises(CookieError, match="Unsupported browser"):
        get_cookies_from_browser("internet_explorer")


# successful extraction tests


def test_returns_required_keys_only() -> None:
    with patch.dict("sys.modules", {"rookiepy": _mock_rookiepy()}):
        result = get_cookies_from_browser("chrome")

    assert set(result.keys()) == set(REQUIRED_COOKIE_KEYS)
    assert result["stel_ssid"] == "abc123"
    assert result["stel_dt"] == "-120"
    assert result["stel_token"] == "tok_xyz"
    assert result["stel_ton_token"] == "ton_xyz"
    assert "unrelated" not in result


def test_default_browser_is_chrome() -> None:
    mock_rp = _mock_rookiepy()
    with patch.dict("sys.modules", {"rookiepy": mock_rp}):
        get_cookies_from_browser()

    mock_rp.chrome.assert_called_once_with(["fragment.com"])


def test_browser_name_is_case_insensitive() -> None:
    mock_rp = _mock_rookiepy()
    with patch.dict("sys.modules", {"rookiepy": mock_rp}):
        result = get_cookies_from_browser("Chrome")

    assert result["stel_ssid"] == "abc123"


# missing cookies tests


def test_missing_cookies_raises() -> None:
    partial_jar = [
        {"name": "stel_ssid", "value": "abc123"},
        {"name": "stel_dt", "value": "-120"},
        # stel_token and stel_ton_token missing
    ]
    with patch.dict("sys.modules", {"rookiepy": _mock_rookiepy(partial_jar)}):
        with pytest.raises(CookieError, match="Fragment cookies not found in chrome"):
            get_cookies_from_browser("chrome")


def test_empty_cookie_value_treated_as_missing() -> None:
    jar_with_empty = [
        {"name": "stel_ssid", "value": "abc123"},
        {"name": "stel_dt", "value": ""},  # empty — should be treated as missing
        {"name": "stel_token", "value": "tok_xyz"},
        {"name": "stel_ton_token", "value": "ton_xyz"},
    ]
    with patch.dict("sys.modules", {"rookiepy": _mock_rookiepy(jar_with_empty)}):
        with pytest.raises(CookieError, match="Fragment cookies not found in chrome"):
            get_cookies_from_browser("chrome")


# read failure tests


def test_browser_read_error_raises() -> None:
    mock_rp = MagicMock()
    mock_rp.chrome.side_effect = PermissionError("locked")
    with patch.dict("sys.modules", {"rookiepy": mock_rp}):
        with pytest.raises(CookieError, match="Failed to read chrome cookies"):
            get_cookies_from_browser("chrome")
