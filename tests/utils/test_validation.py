"""Validation of the client's settings and of the arguments of a purchase."""

import math
from typing import Any

import pytest
from ton_core import MnemonicType

from pyfragment import ConfigurationError, CookieError
from pyfragment.constants.limits import PREMIUM_MONTHS_VALID, STARS_GIVEAWAY_MIN_PER_WINNER, Range
from pyfragment.enums import ApiProvider, GiftAttribute, PaymentMethod, WalletVersion
from pyfragment.utils.validation import (
    check_limit,
    check_months,
    check_stars_winners,
    normalize_confirm_timeout,
    normalize_gift_attributes,
    normalize_max_batch,
    normalize_mnemonic_type,
    parse_cookies,
    parse_enum,
    validate_credentials,
    validate_payment_method,
    validate_seed,
)
from tests.support.data import BIP39_SEED, BIP39_SEED_12_WORDS, COOKIES, SEED, SEED_12_WORDS, TG_ROTATED_SEED


class TestParseCookies:
    def test_dict_is_returned_as_is(self) -> None:
        assert parse_cookies(COOKIES) == COOKIES

    def test_json_string_is_parsed(self) -> None:
        assert parse_cookies('{"stel_token": "a", "stel_ton_token": "b"}') == {"stel_token": "a", "stel_ton_token": "b"}

    @pytest.mark.parametrize("raw", ["not json", "[1, 2]", "null"])
    def test_unreadable_cookies(self, raw: str) -> None:
        with pytest.raises(CookieError, match="Failed to parse"):
            parse_cookies(raw)

    def test_a_non_dict_is_unreadable(self) -> None:
        with pytest.raises(CookieError, match="list"):
            parse_cookies([1])  # type: ignore[arg-type]

    @pytest.mark.parametrize("cookies", [{}, {"stel_token": "a"}, {"stel_token": "a", "stel_ton_token": "  "}])
    def test_missing_or_blank_keys_are_named(self, cookies: dict[str, Any]) -> None:
        with pytest.raises(CookieError, match="stel_ton_token"):
            parse_cookies(cookies)


class TestParseEnum:
    def test_ignores_case_and_spaces(self) -> None:
        assert parse_enum(ApiProvider, "  ToNaPi ", "{value} {supported}") is ApiProvider.TONAPI

    def test_unknown_value_lists_the_supported_ones(self) -> None:
        with pytest.raises(ConfigurationError, match="'nope'.*tonapi"):
            parse_enum(ApiProvider, "nope", ConfigurationError.UNSUPPORTED_PROVIDER)


class TestNormalizeMnemonicType:
    def test_defaults_to_ton(self) -> None:
        assert normalize_mnemonic_type(None, WalletVersion.V5R1) is MnemonicType.TON

    def test_defaults_to_multichain_for_a_telegram_wallet(self) -> None:
        assert normalize_mnemonic_type(None, WalletVersion.TG) is MnemonicType.MULTICHAIN

    def test_explicit_value_is_parsed(self) -> None:
        assert normalize_mnemonic_type(" Multichain ", WalletVersion.V4R2) is MnemonicType.MULTICHAIN

    def test_unknown_value(self) -> None:
        with pytest.raises(ConfigurationError, match="Unsupported mnemonic type 'bip'"):
            normalize_mnemonic_type("bip", WalletVersion.V4R2)


class TestNormalizeGiftAttributes:
    def test_none_is_empty(self) -> None:
        assert normalize_gift_attributes(None) == {}

    def test_names_become_canonical_and_values_a_list(self) -> None:
        result = normalize_gift_attributes({"model": ("Bordeaux",), GiftAttribute.BACKDROP: ["Onyx Black"], "SYMBOL": []})
        assert result == {GiftAttribute.MODEL: ["Bordeaux"], GiftAttribute.BACKDROP: ["Onyx Black"], GiftAttribute.SYMBOL: []}

    def test_unknown_attribute(self) -> None:
        with pytest.raises(ConfigurationError, match="Invalid gift attribute 'rarity'"):
            normalize_gift_attributes({"rarity": ["rare"]})


class TestCheckLimit:
    BOUNDS = Range("count", 1, 5)

    @pytest.mark.parametrize("value", [1, 3, 5])
    def test_accepts_whole_numbers_in_range(self, value: int) -> None:
        check_limit(self.BOUNDS, value)

    @pytest.mark.parametrize("value", [0, 6, -1, True, 2.0, "3", None])
    def test_rejects_everything_else(self, value: object) -> None:
        with pytest.raises(ConfigurationError, match="count"):
            check_limit(self.BOUNDS, value)

    def test_message_states_the_bounds(self) -> None:
        with pytest.raises(ConfigurationError, match="between 1 and 5"):
            check_limit(self.BOUNDS, 9)


class TestCheckStarsWinners:
    @pytest.mark.parametrize(("winners", "amount"), [(5, 500), (10, 1_000), (10_000, 1_000_000), (1, 500)])
    def test_the_most_a_package_allows(self, winners: int, amount: int) -> None:
        check_stars_winners(winners, amount)

    @pytest.mark.parametrize(("winners", "amount"), [(6, 500), (11, 1_000), (10_001, 1_000_000)])
    def test_more_than_the_package_allows(self, winners: int, amount: int) -> None:
        with pytest.raises(ConfigurationError, match="Too many winners") as exc_info:
            check_stars_winners(winners, amount)
        assert f"{amount // STARS_GIVEAWAY_MIN_PER_WINNER:,}" in str(exc_info.value)


class TestCheckMonths:
    @pytest.mark.parametrize("months", sorted(PREMIUM_MONTHS_VALID))
    def test_valid(self, months: int) -> None:
        check_months(months)

    @pytest.mark.parametrize("months", [0, 1, 5, 24, "3", None, 3.0 + 0.5])
    def test_invalid(self, months: object) -> None:
        with pytest.raises(ConfigurationError, match="Premium duration"):
            check_months(months)


class TestValidateCredentials:
    def test_both_present(self) -> None:
        validate_credentials(SEED, "key")

    @pytest.mark.parametrize(
        ("seed", "api_key", "named"),
        [("", "k", "seed"), ("s", "  ", "api_key"), ("", "", "seed, api_key"), (None, "k", "seed")],
    )
    def test_missing_ones_are_named(self, seed: Any, api_key: str, named: str) -> None:
        with pytest.raises(ConfigurationError, match=named):
            validate_credentials(seed, api_key)


class TestValidateSeed:
    @pytest.mark.parametrize("seed", [SEED, SEED_12_WORDS])
    @pytest.mark.parametrize("version", [WalletVersion.V4R2, WalletVersion.V5R1, WalletVersion.HighloadV3R1])
    def test_ton_phrases(self, seed: str, version: WalletVersion) -> None:
        validate_seed(seed, version, MnemonicType.TON)

    @pytest.mark.parametrize("seed", [BIP39_SEED, BIP39_SEED_12_WORDS])
    def test_multichain_phrases(self, seed: str) -> None:
        validate_seed(seed, WalletVersion.V5R1, MnemonicType.MULTICHAIN)

    @pytest.mark.parametrize("seed", [BIP39_SEED_12_WORDS, TG_ROTATED_SEED])
    def test_telegram_wallet_phrases(self, seed: str) -> None:
        validate_seed(seed, WalletVersion.TG, MnemonicType.MULTICHAIN)

    @pytest.mark.parametrize(
        ("seed", "version", "mnemonic_type", "message"),
        [
            (BIP39_SEED, WalletVersion.V5R1, MnemonicType.TON, "checksum for a TON mnemonic"),
            (" ".join(SEED.split()[:-1] + ["abandon"]), WalletVersion.V5R1, MnemonicType.TON, "checksum for a TON mnemonic"),
            (" ".join(["notaword"] * 23 + ["abandon"]), WalletVersion.V5R1, MnemonicType.TON, "Invalid mnemonic word"),
            (SEED, WalletVersion.V5R1, MnemonicType.MULTICHAIN, "checksum for a Multichain"),
            (BIP39_SEED_12_WORDS + " abandon", WalletVersion.TG, MnemonicType.MULTICHAIN, "length: 13"),
            (SEED, WalletVersion.TG, MnemonicType.MULTICHAIN, "TON mnemonics are not supported"),
            (BIP39_SEED_12_WORDS, WalletVersion.TG, MnemonicType.TON, "only Multichain"),
        ],
    )
    def test_rejected_phrases(self, seed: str, version: WalletVersion, mnemonic_type: MnemonicType, message: str) -> None:
        with pytest.raises(ConfigurationError, match=f"Invalid seed phrase.*{message}"):
            validate_seed(seed, version, mnemonic_type)


class TestNormalizeConfirmTimeout:
    @pytest.mark.parametrize(("raw", "expected"), [(0, 0.0), (60, 60.0), (1.5, 1.5)])
    def test_valid(self, raw: float, expected: float) -> None:
        result = normalize_confirm_timeout(raw)
        assert result == expected and isinstance(result, float)

    @pytest.mark.parametrize("raw", [-1, math.inf, math.nan, True, "5", None])
    def test_invalid(self, raw: Any) -> None:
        with pytest.raises(ConfigurationError, match="confirm_timeout"):
            normalize_confirm_timeout(raw)


class TestNormalizeMaxBatch:
    @pytest.mark.parametrize("raw", [1, 10])
    def test_valid(self, raw: int) -> None:
        assert normalize_max_batch(raw) == raw

    @pytest.mark.parametrize("raw", [0, -3, True, 2.0, "2", None])
    def test_invalid(self, raw: Any) -> None:
        with pytest.raises(ConfigurationError, match="max_batch"):
            normalize_max_batch(raw)


class TestValidatePaymentMethod:
    @pytest.mark.parametrize("method", list(PaymentMethod))
    def test_supported(self, method: PaymentMethod) -> None:
        validate_payment_method(method)

    @pytest.mark.parametrize("method", ["btc", "", None])
    def test_unsupported(self, method: Any) -> None:
        with pytest.raises(ConfigurationError, match="Invalid payment method"):
            validate_payment_method(method)
