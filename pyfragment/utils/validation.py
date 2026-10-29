from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation
from typing import Any

from ton_core import MnemonicType as TonMnemonicType

from pyfragment.constants import (
    GRAM_DECIMALS,
    REQUIRED_COOKIE_KEYS,
)
from pyfragment.domains.wallet.wallet import WALLET_CLASSES
from pyfragment.enums import ApiProvider, AuctionFilter, AuctionSort, GiftAttribute, MnemonicType, PaymentMethod, WalletVersion
from pyfragment.exceptions import ConfigurationError, CookieError
from pyfragment.utils.money import to_units


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


def normalize_provider(api_provider: str) -> ApiProvider:
    try:
        return ApiProvider(api_provider.strip().lower())
    except ValueError:
        raise ConfigurationError(
            ConfigurationError.UNSUPPORTED_PROVIDER.format(
                provider=api_provider,
                supported=", ".join(sorted(p.value for p in ApiProvider)),
            )
        ) from None


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


def normalize_mnemonic_type(mnemonic_type: str | None, wallet_version: WalletVersion) -> MnemonicType:
    """The phrase scheme to derive the key with: TON by default, multichain for a Telegram Wallet."""
    if mnemonic_type is None:
        return MnemonicType.MULTICHAIN if wallet_version == WalletVersion.TG else MnemonicType.TON
    try:
        return MnemonicType(mnemonic_type.strip().lower())
    except ValueError:
        raise ConfigurationError(
            ConfigurationError.UNSUPPORTED_MNEMONIC_TYPE.format(
                mnemonic_type=mnemonic_type, supported=", ".join(m.value for m in MnemonicType)
            )
        ) from None


def validate_seed(seed: str, wallet_version: WalletVersion, mnemonic_type: MnemonicType) -> None:
    """Check the phrase's length, words and checksum against the scheme it will be derived with.

    tonutils derives *some* key from any phrase made of known words when it isn't asked to check it: a wrong checksum
    or the wrong scheme silently gives a different wallet, which would only show up as an empty balance.
    """
    try:
        WALLET_CLASSES[wallet_version].validate_mnemonic(seed, TonMnemonicType(mnemonic_type.value))
    except ValueError as exc:
        raise ConfigurationError(ConfigurationError.INVALID_SEED.format(exc=exc)) from None


def normalize_seed(seed: str) -> str:
    """Lower-case the phrase and collapse whitespace: tonutils derives a different wallet from ``Word`` than from ``word``."""
    return " ".join(seed.lower().split())


def normalize_gas_reserve(gas_reserve: Decimal | float | str) -> int:
    """The gas reserve in nanograms. Floats are read through ``str``, so ``0.1`` means exactly 0.1 GRAM (ex TON)."""
    invalid = ConfigurationError(ConfigurationError.INVALID_GAS_RESERVE.format(value=gas_reserve))
    if isinstance(gas_reserve, bool):
        raise invalid
    try:
        amount = Decimal(str(gas_reserve))
    except InvalidOperation:
        raise invalid from None
    if not amount.is_finite() or amount < 0:
        raise invalid
    return to_units(amount, GRAM_DECIMALS)


def normalize_confirm_timeout(confirm_timeout: float) -> float:
    is_number = isinstance(confirm_timeout, (int, float)) and not isinstance(confirm_timeout, bool)
    if not is_number or not math.isfinite(confirm_timeout) or confirm_timeout < 0:
        raise ConfigurationError(ConfigurationError.INVALID_CONFIRM_TIMEOUT.format(value=confirm_timeout))
    return float(confirm_timeout)


def validate_payment_method(payment_method: PaymentMethod) -> None:
    if payment_method not in {m.value for m in PaymentMethod}:
        raise ConfigurationError(
            ConfigurationError.INVALID_PAYMENT_METHOD.format(
                method=payment_method, supported=", ".join(m.value for m in PaymentMethod)
            )
        )
