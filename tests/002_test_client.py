"""Unit tests for FragmentClient — init validation and cookie parsing (no network calls)."""

import json

import pytest

from pyfragment import FragmentClient
from pyfragment.types import ConfigurationError, CookieError

VALID_SEED = "abandon " * 23 + "about"
VALID_API_KEY = "test_api_key"
VALID_COOKIES = {
    "stel_ssid": "x",
    "stel_dt": "x",
    "stel_token": "x",
    "stel_ton_token": "x",
}


def test_valid_init() -> None:
    client = FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES)
    assert client.seed == VALID_SEED.strip()
    assert client.api_key == VALID_API_KEY
    assert client.wallet_version == "V5R1"


def test_wallet_version_v4r2() -> None:
    client = FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES, wallet_version="V4R2")
    assert client.wallet_version == "V4R2"


def test_wallet_version_is_case_insensitive() -> None:
    client = FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES, wallet_version="v5r1")
    assert client.wallet_version == "V5R1"


def test_missing_seed_raises() -> None:
    with pytest.raises(ConfigurationError):
        FragmentClient(seed="", api_key=VALID_API_KEY, cookies=VALID_COOKIES)


def test_whitespace_only_seed_raises() -> None:
    with pytest.raises(ConfigurationError):
        FragmentClient(seed="   ", api_key=VALID_API_KEY, cookies=VALID_COOKIES)


def test_missing_api_key_raises() -> None:
    with pytest.raises(ConfigurationError):
        FragmentClient(seed=VALID_SEED, api_key="", cookies=VALID_COOKIES)


def test_unsupported_wallet_version_raises() -> None:
    with pytest.raises(ConfigurationError):
        FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES, wallet_version="V3R2")


def test_cookies_as_json_string() -> None:
    client = FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=json.dumps(VALID_COOKIES))
    assert client.cookies == VALID_COOKIES


def test_invalid_cookies_json_raises() -> None:
    with pytest.raises(CookieError):
        FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies="{not valid json}")


def test_missing_cookie_key_raises() -> None:
    with pytest.raises(CookieError):
        FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies={"stel_ssid": "x"})


def test_empty_cookie_value_raises() -> None:
    bad = {**VALID_COOKIES, "stel_token": ""}
    with pytest.raises(CookieError):
        FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=bad)


def test_whitespace_cookie_value_raises() -> None:
    bad = {**VALID_COOKIES, "stel_ton_token": "   "}
    with pytest.raises(CookieError):
        FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=bad)
