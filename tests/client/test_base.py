"""BaseClient / FragmentClient: argument validation, defaults, repr, lifecycle and the raw ``call``."""

import json
from typing import Any
from unittest.mock import AsyncMock

import pytest
from ton_core import multichain_mnemonic_new

from pyfragment import ConfigurationError, CookieError, FragmentClient
from pyfragment.constants.fragment import BASE_HEADERS, FRAGMENT_BASE_URL, PREMIUM_PAGE, REQUIRED_COOKIE_KEYS
from pyfragment.enums import ApiMethod, ApiProvider, MnemonicType, WalletVersion
from tests.support import fixtures
from tests.support.data import (
    API_KEY,
    BIP39_SEED,
    BIP39_SEED_12_WORDS,
    COOKIES,
    SEED,
    SEED_12_WORDS,
    TG_ROTATED_SEED,
)
from tests.support.fake_fragment import FakeFragment


def make(**options: Any) -> FragmentClient:
    options.setdefault("seed", SEED)
    options.setdefault("api_key", API_KEY)
    options.setdefault("cookies", COOKIES)
    return FragmentClient(**options)


class TestDefaults:
    def test_a_minimal_client(self) -> None:
        client = make()

        assert client.seed == SEED
        assert client.api_key == API_KEY
        assert client.wallet_version == WalletVersion.V5R1
        assert client.mnemonic_type == MnemonicType.TON
        assert client.api_provider == ApiProvider.TONAPI
        assert client.timeout == 30.0
        assert client.confirm_timeout == 60.0
        assert client.max_batch == 1
        assert client.on_transfer_prepared is None
        assert client.transfer_coordinator is None
        assert client.headers == BASE_HEADERS

    def test_the_api_key_is_stripped(self) -> None:
        assert make(api_key=f"  {API_KEY}\n").api_key == API_KEY

    def test_default_headers_are_a_copy_not_shared_across_clients(self) -> None:
        first, second = make(), make()

        first.headers["x-test"] = "first"

        assert first.headers is not BASE_HEADERS
        assert "x-test" not in second.headers
        assert "x-test" not in BASE_HEADERS

    def test_custom_headers_are_copied_not_referenced(self) -> None:
        source = {"x-test": "source"}
        client = make(headers=source)

        client.headers["x-test"] = "changed"

        assert source == {"x-test": "source"}

    def test_custom_headers_replace_the_defaults(self) -> None:
        assert make(headers={"x-test": "1"}).headers == {"x-test": "1"}


class TestApiProvider:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("tonapi", ApiProvider.TONAPI),
            ("toncenter", ApiProvider.TONCENTER),
            ("TONAPI", ApiProvider.TONAPI),
            (" TonCenter ", ApiProvider.TONCENTER),
        ],
    )
    def test_is_case_insensitive(self, value: str, expected: ApiProvider) -> None:
        assert make(api_provider=value).api_provider == expected

    def test_an_unknown_provider_lists_the_supported_ones(self) -> None:
        with pytest.raises(ConfigurationError, match="Unsupported API provider 'infura'.*toncenter, tonapi|tonapi, toncenter"):
            make(api_provider="infura")


class TestWalletVersion:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("V4R2", WalletVersion.V4R2),
            ("v5r1", WalletVersion.V5R1),
            ("highloadv2", WalletVersion.HighloadV2),
            ("HIGHLOADV3R1", WalletVersion.HighloadV3R1),
        ],
    )
    def test_is_case_insensitive(self, value: str, expected: WalletVersion) -> None:
        assert make(wallet_version=value).wallet_version == expected

    def test_an_unsupported_version_is_rejected(self) -> None:
        with pytest.raises(ConfigurationError, match="Unsupported wallet version 'V3R2'"):
            make(wallet_version="V3R2")


class TestSeed:
    @pytest.mark.parametrize(("seed", "words"), [(SEED_12_WORDS, 12), (SEED, 24)])
    def test_ton_phrases_of_both_lengths(self, seed: str, words: int) -> None:
        assert len(make(seed=seed).seed.split()) == words

    @pytest.mark.parametrize("seed", ["", "   "])
    def test_a_blank_seed_is_missing(self, seed: str) -> None:
        with pytest.raises(ConfigurationError, match="seed"):
            make(seed=seed)

    @pytest.mark.parametrize("api_key", ["", "   "])
    def test_a_blank_api_key_is_missing(self, api_key: str) -> None:
        with pytest.raises(ConfigurationError, match="api_key"):
            make(api_key=api_key)

    def test_both_missing_are_reported_together(self) -> None:
        with pytest.raises(ConfigurationError, match="seed, api_key"):
            make(seed="", api_key="")

    def test_case_and_whitespace_of_the_phrase_do_not_change_the_wallet(self) -> None:
        messy = "  " + SEED.upper().replace(" ", "\n ", 3) + "\t"

        assert make(seed=messy).ton_wallet.address == make().ton_wallet.address

    @pytest.mark.parametrize(
        ("seed", "options", "message"),
        [
            (" ".join(["word"] * 23), {}, "Invalid mnemonic length: 23"),
            (BIP39_SEED, {}, "checksum for a TON mnemonic.*Multichain"),
            (" ".join(SEED.split()[:-1] + ["abandon"]), {}, "checksum for a TON mnemonic"),
            (" ".join(["notaword"] * 23 + ["abandon"]), {}, "Invalid mnemonic word"),
            (SEED, {"mnemonic_type": "multichain"}, "checksum for a Multichain"),
            (BIP39_SEED_12_WORDS + " abandon", {"wallet_version": "TG"}, "length: 13"),
            (BIP39_SEED_12_WORDS + " " + " ".join(["zoo"] * 12), {"wallet_version": "TG"}, "words 13-24"),
            (SEED, {"wallet_version": "TG"}, "TON mnemonics are not supported"),
            (BIP39_SEED_12_WORDS, {"wallet_version": "TG", "mnemonic_type": "ton"}, "only Multichain"),
        ],
        ids=[
            "wrong-length",
            "bip39-as-ton",
            "wrong-checksum",
            "not-in-wordlist",
            "ton-as-multichain",
            "tg-length",
            "tg-second-half",
            "tg-ton-phrase",
            "tg-ton-scheme",
        ],
    )
    def test_an_invalid_phrase_is_rejected_with_the_reason(self, seed: str, options: dict[str, str], message: str) -> None:
        with pytest.raises(ConfigurationError, match="Invalid seed phrase: .*" + message):
            make(seed=seed, **options)


class TestMnemonicType:
    def test_defaults_to_ton(self) -> None:
        assert make().mnemonic_type == MnemonicType.TON

    def test_a_telegram_wallet_uses_multichain_phrases(self) -> None:
        client = make(seed=BIP39_SEED_12_WORDS, wallet_version="tg")

        assert client.wallet_version == WalletVersion.TG
        assert client.mnemonic_type == MnemonicType.MULTICHAIN

    def test_a_telegram_wallet_accepts_a_rotated_24_word_phrase(self) -> None:
        assert make(seed=TG_ROTATED_SEED, wallet_version="TG").seed == TG_ROTATED_SEED

    @pytest.mark.parametrize("words", [12, 15, 18, 21, 24])
    def test_multichain_phrases_of_every_bip39_length(self, words: int) -> None:
        seed = " ".join(multichain_mnemonic_new(words))

        assert make(seed=seed, mnemonic_type="Multichain").mnemonic_type == MnemonicType.MULTICHAIN

    @pytest.mark.parametrize(
        "version", [WalletVersion.V4R2, WalletVersion.V5R1, WalletVersion.HighloadV2, WalletVersion.HighloadV3R1]
    )
    def test_a_multichain_phrase_works_with_every_wallet_contract(self, version: WalletVersion) -> None:
        client = make(seed=BIP39_SEED, wallet_version=version, mnemonic_type="multichain")

        assert client.wallet_version == version

    def test_an_unknown_type_is_rejected(self) -> None:
        with pytest.raises(ConfigurationError, match="Unsupported mnemonic type 'bip44'"):
            make(mnemonic_type="bip44")


class TestCookies:
    def test_a_json_string_is_parsed(self) -> None:
        assert make(cookies=json.dumps(COOKIES)).cookies == COOKIES

    def test_only_the_required_cookies_are_needed(self) -> None:
        cookies = {key: "x" for key in REQUIRED_COOKIE_KEYS}

        assert make(cookies=cookies).cookies == cookies

    @pytest.mark.parametrize("missing", REQUIRED_COOKIE_KEYS)
    def test_each_required_cookie_is_required(self, missing: str) -> None:
        cookies = {key: value for key, value in COOKIES.items() if key != missing}

        with pytest.raises(CookieError, match=missing):
            make(cookies=cookies)

    @pytest.mark.parametrize("value", ["", "   "])
    def test_a_blank_cookie_value_counts_as_missing(self, value: str) -> None:
        with pytest.raises(CookieError, match="stel_token"):
            make(cookies={**COOKIES, "stel_token": value})

    def test_a_cookie_missing_from_the_dict_is_reported_by_name(self) -> None:
        with pytest.raises(CookieError, match="stel_token, stel_ton_token"):
            make(cookies={"stel_ssid": "x"})

    def test_malformed_json_is_a_cookie_error(self) -> None:
        with pytest.raises(CookieError, match="Failed to parse cookies"):
            make(cookies="{not valid json}")

    @pytest.mark.parametrize("cookies", ['["stel_ssid"]', "42", '"text"'])
    def test_json_that_is_not_an_object_is_a_cookie_error(self, cookies: str) -> None:
        with pytest.raises(CookieError, match="Failed to parse cookies"):
            make(cookies=cookies)


class TestTimings:
    @pytest.mark.parametrize("value", [0, 0.0, 5, 60.5])
    def test_a_confirm_timeout_is_kept_as_a_float(self, value: float) -> None:
        client = make(confirm_timeout=value)

        assert client.confirm_timeout == value and isinstance(client.confirm_timeout, float)

    @pytest.mark.parametrize("value", [-1, float("inf"), float("nan"), "60", None, True])
    def test_an_invalid_confirm_timeout_is_rejected(self, value: object) -> None:
        with pytest.raises(ConfigurationError, match="confirm_timeout"):
            make(confirm_timeout=value)

    @pytest.mark.parametrize("value", [1, 2, 255])
    def test_max_batch_is_kept(self, value: int) -> None:
        assert make(max_batch=value).max_batch == value

    @pytest.mark.parametrize("value", [0, -1, 2.0, True, "5", None])
    def test_an_invalid_max_batch_is_rejected(self, value: object) -> None:
        with pytest.raises(ConfigurationError, match="max_batch"):
            make(max_batch=value)

    def test_the_timeout_reaches_the_transport(self) -> None:
        assert make(timeout=7.5)._transport._timeout == 7.5


class TestRepr:
    def test_names_the_setup_without_secrets(self) -> None:
        text = repr(make())

        assert text.startswith("FragmentClient(")
        assert WalletVersion.V5R1 in text and MnemonicType.TON in text and ApiProvider.TONAPI in text
        assert f"cookies={len(COOKIES)} keys" in text
        assert SEED not in text and API_KEY not in text and "stel_token" not in text


class TestLifecycle:
    async def test_async_with_returns_the_client_and_closes_it(self) -> None:
        client = make()
        client._transport.aclose = AsyncMock()

        async with client as entered:
            assert entered is client
            client._transport.aclose.assert_not_awaited()

        client._transport.aclose.assert_awaited_once()

    async def test_aclose_is_idempotent(self) -> None:
        client = make()

        await client.aclose()
        await client.aclose()

    async def test_the_wallet_is_closed_even_if_the_transport_fails_to_close(self) -> None:
        client = make()
        client._transport.aclose = AsyncMock(side_effect=RuntimeError("boom"))
        client.ton_wallet.aclose = AsyncMock()

        with pytest.raises(RuntimeError, match="boom"):
            await client.aclose()

        client.ton_wallet.aclose.assert_awaited_once()

    async def test_leaving_async_with_closes_even_when_the_body_raises(self) -> None:
        client = make()
        client._transport.aclose = AsyncMock()

        with pytest.raises(ValueError, match="body"):
            async with client:
                raise ValueError("body")

        client._transport.aclose.assert_awaited_once()


class TestCall:
    async def test_returns_the_parsed_response(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply("anyMethod", {"key": "value"})

        assert await client.call("anyMethod", {"a": 1}) == {"key": "value"}

    async def test_an_error_body_comes_back_untouched(self, client: FragmentClient, fragment: FakeFragment) -> None:
        body = fixtures.response("invalid_method.json")
        fragment.reply("nope", body)

        assert await client.call("nope") == body

    async def test_forwards_method_data_and_page(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply(ApiMethod.SEARCH_PREMIUM_GIFT_RECIPIENT, {})

        await client.call(ApiMethod.SEARCH_PREMIUM_GIFT_RECIPIENT, {"query": "x"}, page_url=PREMIUM_PAGE)

        (call,) = fragment.calls
        assert (call.method, call.data, call.page_url) == (
            ApiMethod.SEARCH_PREMIUM_GIFT_RECIPIENT,
            {"query": "x"},
            PREMIUM_PAGE,
        )

    async def test_defaults_to_no_data_on_the_base_page(self, client: FragmentClient, fragment: FakeFragment) -> None:
        fragment.reply("anyMethod", {})

        await client.call("anyMethod")

        (call,) = fragment.calls
        assert (call.data, call.page_url) == ({}, FRAGMENT_BASE_URL)
