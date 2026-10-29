"""Validate FragmentClient setup, cookie parsing, and wallet version checks."""

import json
from decimal import Decimal

import pytest

from pyfragment import ConfigurationError, CookieError, FragmentClient
from pyfragment.constants import BASE_HEADERS, GRAM_DECIMALS
from pyfragment.enums import ApiProvider, MnemonicType, WalletVersion
from tests.shared import (
    BIP39_SEED,
    BIP39_SEED_12_WORDS,
    TG_ROTATED_SEED,
    VALID_API_KEY,
    VALID_COOKIES,
    VALID_SEED,
    VALID_SEED_12_WORDS,
)

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
    bad = {**VALID_COOKIES, "stel_token": "   "}
    with pytest.raises(CookieError):
        FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=bad)


def test_repr() -> None:
    client = FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES)
    r = repr(client)
    assert "FragmentClient" in r
    assert WalletVersion.V5R1 in r
    assert ApiProvider.TONAPI in r
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


# Wallet kinds and phrase schemes


@pytest.mark.parametrize(
    ("seed", "options", "message"),
    [
        (BIP39_SEED, {}, "checksum for a TON mnemonic.*Multichain"),  # a multichain phrase without mnemonic_type
        (" ".join(VALID_SEED.split()[:-1] + ["abandon"]), {}, "checksum for a TON mnemonic"),
        (" ".join(["notaword"] * 23 + ["abandon"]), {}, "Invalid mnemonic word"),
        (VALID_SEED, {"mnemonic_type": "multichain"}, "checksum for a Multichain"),
        (BIP39_SEED_12_WORDS + " abandon", {"wallet_version": "TG"}, "length: 13"),
        (BIP39_SEED_12_WORDS + " " + " ".join(["zoo"] * 12), {"wallet_version": "TG"}, "words 13-24"),
        (VALID_SEED, {"wallet_version": "TG"}, "TON mnemonics are not supported"),
        (BIP39_SEED_12_WORDS, {"wallet_version": "TG", "mnemonic_type": "ton"}, "only Multichain"),
    ],
    ids=[
        "bip39-as-ton",
        "wrong-word",
        "not-in-wordlist",
        "ton-as-multichain",
        "tg-length",
        "tg-second-half",
        "tg-ton-phrase",
        "tg-ton-scheme",
    ],
)
def test_invalid_seed_phrase_raises(seed: str, options: dict[str, str], message: str) -> None:
    with pytest.raises(ConfigurationError, match="Invalid seed phrase: .*" + message):
        FragmentClient(seed=seed, api_key=VALID_API_KEY, cookies=VALID_COOKIES, **options)  # type: ignore[arg-type]


def _client(**options: object) -> FragmentClient:
    options.setdefault("seed", VALID_SEED)
    return FragmentClient(api_key=VALID_API_KEY, cookies=VALID_COOKIES, **options)  # type: ignore[arg-type]


def test_phrase_scheme_defaults_to_ton() -> None:
    assert _client().mnemonic_type == MnemonicType.TON


def test_telegram_wallet_uses_multichain_phrases() -> None:
    client = _client(seed=BIP39_SEED_12_WORDS, wallet_version="tg")
    assert client.wallet_version == WalletVersion.TG
    assert client.mnemonic_type == MnemonicType.MULTICHAIN


def test_telegram_wallet_accepts_a_rotated_24_word_phrase() -> None:
    assert _client(seed=TG_ROTATED_SEED, wallet_version="TG").seed == TG_ROTATED_SEED


@pytest.mark.parametrize("words", [12, 15, 18, 21, 24])
def test_multichain_phrases_of_every_bip39_length_are_accepted(words: int) -> None:
    from ton_core import multichain_mnemonic_new

    seed = " ".join(multichain_mnemonic_new(words))
    assert _client(seed=seed, mnemonic_type="Multichain").mnemonic_type == MnemonicType.MULTICHAIN


def test_unknown_mnemonic_type_raises() -> None:
    with pytest.raises(ConfigurationError, match="Unsupported mnemonic type 'bip44'"):
        _client(mnemonic_type="bip44")


@pytest.mark.parametrize("version", ["V4R2", "V5R1", "HighloadV2", "HighloadV3R1"])
def test_multichain_phrase_works_with_every_wallet_contract(version: str) -> None:
    assert _client(seed=BIP39_SEED, wallet_version=version, mnemonic_type="multichain").wallet_version == version


# Money and timing options


@pytest.mark.parametrize(
    ("gas_reserve", "nano"), [("0.33", 330_000_000), (0.1, 100_000_000), (Decimal("0"), 0), (1, 10**GRAM_DECIMALS)]
)
def test_gas_reserve_is_exact(gas_reserve: object, nano: int) -> None:
    assert _client(gas_reserve=gas_reserve).gas_reserve_nano == nano


@pytest.mark.parametrize("gas_reserve", ["-0.1", "abc", "1,5", float("nan"), True])
def test_invalid_gas_reserve_raises(gas_reserve: object) -> None:
    with pytest.raises(ConfigurationError, match="gas_reserve"):
        _client(gas_reserve=gas_reserve)


@pytest.mark.parametrize("confirm_timeout", [-1, float("inf"), "60", None])
def test_invalid_confirm_timeout_raises(confirm_timeout: object) -> None:
    with pytest.raises(ConfigurationError, match="confirm_timeout"):
        _client(confirm_timeout=confirm_timeout)


@pytest.mark.parametrize("cookies", ['["stel_ssid"]', "42", '"text"'])
def test_cookies_json_that_is_not_an_object_raises_cookie_error(cookies: str) -> None:
    with pytest.raises(CookieError, match="Failed to parse cookies"):
        FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=cookies)
