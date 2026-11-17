from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any, TypeVar

from pyfragment.constants import LIMITS, PREMIUM_MONTHS_VALID, REQUIRED_COOKIE_KEYS
from pyfragment.domains.wallet.wallet import WALLET_CLASSES
from pyfragment.enums import (
    ApiProvider,
    AuctionFilter,
    AuctionSort,
    GiftAttribute,
    Limit,
    MnemonicType,
    PaymentMethod,
    WalletVersion,
)
from pyfragment.exceptions import ConfigurationError, CookieError


def parse_cookies(cookies: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(cookies, str):
        try:
            cookies = json.loads(cookies)
        except Exception as exc:
            raise CookieError(CookieError.READ_FAILED.format(exc=exc)) from exc
    if not isinstance(cookies, dict):
        raise CookieError(CookieError.READ_FAILED.format(exc=type(cookies).__name__))
    return cookies


def validate_cookie_keys(cookies: dict[str, Any]) -> None:
    missing = [k for k in REQUIRED_COOKIE_KEYS if not str(cookies.get(k, "")).strip()]
    if missing:
        raise CookieError(CookieError.MISSING_KEYS.format(keys=", ".join(missing)))


E = TypeVar("E", bound=Enum)


def parse_enum(enum: type[E], raw: str, error: str) -> E:
    """The member of ``enum`` whose value is ``raw``, ignoring case and surrounding spaces."""
    members = {str(member.value).lower(): member for member in enum}
    try:
        return members[raw.strip().lower()]
    except KeyError:
        supported = ", ".join(sorted(str(member.value) for member in enum))
        raise ConfigurationError(error.format(value=raw, supported=supported)) from None


def normalize_provider(api_provider: str) -> ApiProvider:
    return parse_enum(ApiProvider, api_provider, ConfigurationError.UNSUPPORTED_PROVIDER)


def normalize_wallet_version(wallet_version: str) -> WalletVersion:
    return parse_enum(WalletVersion, wallet_version, ConfigurationError.UNSUPPORTED_VERSION)


def normalize_mnemonic_type(mnemonic_type: str | None, wallet_version: WalletVersion) -> MnemonicType:
    """The phrase scheme to derive the key with: TON by default, multichain for a Telegram Wallet."""
    if mnemonic_type is None:
        return MnemonicType.MULTICHAIN if wallet_version == WalletVersion.TG else MnemonicType.TON
    return parse_enum(MnemonicType, mnemonic_type, ConfigurationError.UNSUPPORTED_MNEMONIC_TYPE)


def normalize_sort(sort: str | None) -> AuctionSort | None:
    return None if sort is None else parse_enum(AuctionSort, sort, ConfigurationError.INVALID_SORT)


def normalize_filter(filter: str | None) -> AuctionFilter | None:
    return None if filter is None else parse_enum(AuctionFilter, filter, ConfigurationError.INVALID_FILTER)


def normalize_gift_attributes(attr: Mapping[str, Sequence[str]] | None) -> dict[GiftAttribute, list[str]]:
    return {
        parse_enum(GiftAttribute, name, ConfigurationError.INVALID_GIFT_ATTRIBUTE): list(values)
        for name, values in (attr or {}).items()
    }


def check_limit(limit: Limit, value: object) -> None:
    bounds = LIMITS[limit]
    if not is_int_in_range(value, bounds.min, bounds.max):
        raise ConfigurationError(ConfigurationError.OUT_OF_RANGE.format(label=bounds.label, min=bounds.min, max=bounds.max))


def check_months(months: object) -> None:
    if months not in PREMIUM_MONTHS_VALID:
        raise ConfigurationError(ConfigurationError.INVALID_MONTHS)


def is_int_in_range(value: object, low: int, high: int) -> bool:
    # bool is a subclass of int, but `True` is never a meaningful amount or count.
    return isinstance(value, int) and not isinstance(value, bool) and low <= value <= high


def validate_credentials(seed: str, api_key: str) -> None:
    missing = [name for name, val in (("seed", seed), ("api_key", api_key)) if not val or not str(val).strip()]
    if missing:
        raise ConfigurationError(ConfigurationError.MISSING_VARS.format(keys=", ".join(missing)))


def validate_seed(seed: str, wallet_version: WalletVersion, mnemonic_type: MnemonicType) -> None:
    """Check the phrase's length, words and checksum against the scheme it will be derived with.

    tonutils derives *some* key from any phrase made of known words when it isn't asked to check it: a wrong checksum
    or the wrong scheme silently gives a different wallet, which would only show up as an empty balance.
    """
    try:
        WALLET_CLASSES[wallet_version].validate_mnemonic(seed, mnemonic_type)
    except ValueError as exc:
        raise ConfigurationError(ConfigurationError.INVALID_SEED.format(exc=exc)) from None


def normalize_confirm_timeout(confirm_timeout: float) -> float:
    is_number = isinstance(confirm_timeout, (int, float)) and not isinstance(confirm_timeout, bool)
    if not is_number or not math.isfinite(confirm_timeout) or confirm_timeout < 0:
        raise ConfigurationError(ConfigurationError.INVALID_CONFIRM_TIMEOUT.format(value=confirm_timeout))
    return float(confirm_timeout)


def normalize_max_batch(max_batch: int) -> int:
    if not isinstance(max_batch, int) or isinstance(max_batch, bool) or max_batch < 1:
        raise ConfigurationError(ConfigurationError.INVALID_MAX_BATCH.format(value=max_batch))
    return max_batch


def validate_payment_method(payment_method: PaymentMethod) -> None:
    if payment_method not in {m.value for m in PaymentMethod}:
        raise ConfigurationError(
            ConfigurationError.INVALID_PAYMENT_METHOD.format(
                method=payment_method, supported=", ".join(m.value for m in PaymentMethod)
            )
        )
