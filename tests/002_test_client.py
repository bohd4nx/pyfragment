"""Validate FragmentClient setup, cookie parsing, and wallet version checks."""

import json

import pytest

from pyfragment import ConfigurationError, CookieError, FragmentClient
from pyfragment.core.constants import BASE_HEADERS
from pyfragment.enums import ApiProvider, WalletVersion
from tests.shared import BIP39_SEED, VALID_API_KEY, VALID_COOKIES, VALID_SEED, VALID_SEED_12_WORDS

# Client init tests


def test_valid_init() -> None:
    client = FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES)
    assert client.seed == VALID_SEED.strip()
    assert client.api_key == VALID_API_KEY
    assert client.wallet_version == WalletVersion.V5R1
    assert client.api_provider == ApiProvider.TONAPI


def test_default_headers_are_a_copy_not_shared_across_clients() -> None:
    client_a = FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES)
    client_b = FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES)

    client_a.headers["x-test"] = "client-a"

    assert client_a.headers is not BASE_HEADERS
    assert "x-test" not in client_b.headers
    assert "x-test" not in BASE_HEADERS


def test_custom_headers_are_copied_not_referenced() -> None:
    source = {"x-test": "source"}
    client = FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES, headers=source)

    client.headers["x-test"] = "changed"

    assert source["x-test"] == "source"


# API provider tests


def test_api_provider_default_is_tonapi() -> None:
    client = FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES)
    assert client.api_provider == ApiProvider.TONAPI


def test_api_provider_toncenter() -> None:
    client = FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES, api_provider="toncenter")
    assert client.api_provider == ApiProvider.TONCENTER


def test_api_provider_is_case_insensitive() -> None:
    client = FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES, api_provider="TONAPI")
    assert client.api_provider == ApiProvider.TONAPI


def test_unsupported_api_provider_raises() -> None:
    with pytest.raises(ConfigurationError):
        FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES, api_provider="infura")


# Wallet version tests


def test_wallet_version_v4r2() -> None:
    client = FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES, wallet_version="V4R2")
    assert client.wallet_version == WalletVersion.V4R2


def test_wallet_version_is_case_insensitive() -> None:
    client = FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES, wallet_version="v5r1")
    assert client.wallet_version == WalletVersion.V5R1


@pytest.mark.parametrize("version", ["HighloadV2", "highloadv2", "HighloadV3R1", "HIGHLOADV3R1"])
def test_wallet_version_highload_variants(version: str) -> None:
    client = FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES, wallet_version=version)
    assert client.wallet_version.lower() == version.lower()


def test_unsupported_wallet_version_raises() -> None:
    with pytest.raises(ConfigurationError):
        FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES, wallet_version="V3R2")


# Seed and mnemonic validation tests


def test_missing_seed_raises() -> None:
    with pytest.raises(ConfigurationError):
        FragmentClient(seed="", api_key=VALID_API_KEY, cookies=VALID_COOKIES)


def test_both_seed_and_api_key_missing_raises() -> None:
    with pytest.raises(ConfigurationError):
        FragmentClient(seed="", api_key="", cookies=VALID_COOKIES)


def test_whitespace_only_seed_raises() -> None:
    with pytest.raises(ConfigurationError):
        FragmentClient(seed="   ", api_key=VALID_API_KEY, cookies=VALID_COOKIES)


def test_invalid_mnemonic_length_raises() -> None:
    bad_seed = " ".join(["word"] * 23)
    with pytest.raises(ConfigurationError):
        FragmentClient(seed=bad_seed, api_key=VALID_API_KEY, cookies=VALID_COOKIES)


@pytest.mark.parametrize(("seed", "length"), [(VALID_SEED_12_WORDS, 12), (VALID_SEED, 24)])
def test_valid_mnemonic_lengths(seed: str, length: int) -> None:
    client = FragmentClient(seed=seed, api_key=VALID_API_KEY, cookies=VALID_COOKIES)
    assert len(client.seed.split()) == length


def test_seed_is_normalized() -> None:
    messy = "  " + VALID_SEED.upper().replace(" ", "\n ", 3) + "\t"
    client = FragmentClient(seed=messy, api_key=VALID_API_KEY, cookies=VALID_COOKIES)
    assert client.seed == VALID_SEED


@pytest.mark.parametrize(
    "seed",
    [
        BIP39_SEED,  # right length and words, but not a TON phrase
        " ".join(VALID_SEED.split()[:-1] + ["abandon"]),  # one word replaced -> wrong checksum
        " ".join(["notaword"] * 24),
    ],
    ids=["bip39", "wrong-word", "not-in-wordlist"],
)
def test_invalid_mnemonic_phrase_raises(seed: str) -> None:
    with pytest.raises(ConfigurationError, match="not a valid TON wallet phrase"):
        FragmentClient(seed=seed, api_key=VALID_API_KEY, cookies=VALID_COOKIES)


# API key validation tests


def test_missing_api_key_raises() -> None:
    with pytest.raises(ConfigurationError):
        FragmentClient(seed=VALID_SEED, api_key="", cookies=VALID_COOKIES)


# Cookie validation tests


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


def test_repr() -> None:
    client = FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES)
    r = repr(client)
    assert "FragmentClient" in r
    assert "V5R1" in r
    assert "tonapi" in r
    assert "4 keys" in r


@pytest.mark.asyncio
async def test_async_context_manager() -> None:
    async with FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES) as client:
        assert isinstance(client, FragmentClient)


@pytest.mark.asyncio
async def test_aclose_is_idempotent() -> None:
    client = FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES)
    await client.aclose()
    await client.aclose()
