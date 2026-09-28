from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any, cast

from ton_core import is_basic_seed, mnemonic_to_entropy

from pyfragment.core.constants import MNEMONIC_WORD_COUNTS_VALID, REQUIRED_COOKIE_KEYS
from pyfragment.enums import ApiProvider, AuctionFilter, AuctionSort, GiftAttribute, WalletVersion
from pyfragment.exceptions import ConfigurationError, CookieError


def parse_cookies(cookies: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(cookies, str):
        try:
            cookies = json.loads(cookies)
        except Exception as exc:
            raise CookieError(CookieError.READ_FAILED.format(exc=exc)) from exc
    return cast(dict[str, Any], cookies)


def validate_cookie_keys(cookies: dict[str, Any]) -> None:
    missing = [k for k in REQUIRED_COOKIE_KEYS if not str(cookies.get(k, "")).strip()]
    if missing:
        raise CookieError(CookieError.MISSING_KEYS.format(keys=", ".join(missing)))


def normalize_provider(api_provider: str) -> ApiProvider:
    try:
        return ApiProvider(api_provider.strip().lower())
    except ValueError:
        raise ConfigurationError(
            ConfigurationError.UNSUPPORTED_PROVIDER.format(
                provider=api_provider,
                supported=", ".join(sorted(p.value for p in ApiProvider)),
            )
        )


def normalize_wallet_version(wallet_version: str) -> WalletVersion:
    version = wallet_version.strip()
    for member in WalletVersion:
        if member.value.lower() == version.lower():
            return member
    raise ConfigurationError(
        ConfigurationError.UNSUPPORTED_VERSION.format(
            version=version,
            supported=", ".join(sorted(m.value for m in WalletVersion)),
        )
    )


def normalize_sort(sort: str | None) -> AuctionSort | None:
    if sort is None:
        return None
    try:
        return AuctionSort(sort.strip().lower())
    except ValueError:
        raise ConfigurationError(
            ConfigurationError.INVALID_SORT.format(sort=sort, supported=", ".join(m.value for m in AuctionSort))
        ) from None


def normalize_filter(filter: str | None) -> AuctionFilter | None:
    if filter is None:
        return None
    try:
        return AuctionFilter(filter.strip().lower())
    except ValueError:
        raise ConfigurationError(
            ConfigurationError.INVALID_FILTER.format(filter=filter, supported=", ".join(repr(m.value) for m in AuctionFilter))
        ) from None


def normalize_gift_attributes(attr: Mapping[str, Sequence[str]] | None) -> dict[GiftAttribute, list[str]]:
    normalized: dict[GiftAttribute, list[str]] = {}
    for name, values in (attr or {}).items():
        try:
            trait = GiftAttribute(name.strip().title())
        except ValueError:
            raise ConfigurationError(
                ConfigurationError.INVALID_GIFT_ATTRIBUTE.format(
                    attribute=name, supported=", ".join(m.value for m in GiftAttribute)
                )
            ) from None
        normalized[trait] = list(values)
    return normalized


def is_int_in_range(value: object, low: int, high: int) -> bool:
    # bool is a subclass of int, but `True` is never a meaningful amount or count.
    return isinstance(value, int) and not isinstance(value, bool) and low <= value <= high


def validate_credentials(seed: str, api_key: str) -> None:
    missing = [name for name, val in (("seed", seed), ("api_key", api_key)) if not val or not str(val).strip()]
    if missing:
        raise ConfigurationError(ConfigurationError.MISSING_VARS.format(keys=", ".join(missing)))

    words = normalize_seed(seed).split()
    if len(words) not in MNEMONIC_WORD_COUNTS_VALID:
        raise ConfigurationError(ConfigurationError.INVALID_MNEMONIC.format(count=len(words)))
    # tonutils only rejects words outside the BIP39 list: a wrong checksum, a BIP39-style phrase or a
    # password-protected one silently derives a different wallet, which would only show up as an empty balance.
    if not is_basic_seed(mnemonic_to_entropy(words)):
        raise ConfigurationError(ConfigurationError.INVALID_MNEMONIC_PHRASE)


def normalize_seed(seed: str) -> str:
    """Lower-case the phrase and collapse whitespace: tonutils derives a different wallet from ``Word`` than from ``word``."""
    return " ".join(seed.lower().split())
