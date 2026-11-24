from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any, TypeVar

from pyfragment.constants.fragment import REQUIRED_COOKIE_KEYS
from pyfragment.constants.limits import PREMIUM_MONTHS_VALID, STARS_GIVEAWAY_MIN_PER_WINNER, Range
from pyfragment.domains.wallet.wallet import WALLET_CLASSES
from pyfragment.enums import (
    GiftAttribute,
    MnemonicType,
    PaymentMethod,
    WalletVersion,
)
from pyfragment.exceptions import ConfigurationError, CookieError


def parse_cookies(cookies: dict[str, Any] | str) -> dict[str, Any]:
    """The cookies as a dict (they may be given as a JSON string), checked for the keys Fragment needs."""
    if isinstance(cookies, str):
        try:
            cookies = json.loads(cookies)
        except Exception as exc:
            raise CookieError(CookieError.READ_FAILED.format(exc=exc)) from exc
    if not isinstance(cookies, dict):
        raise CookieError(CookieError.READ_FAILED.format(exc=type(cookies).__name__))
    missing = [k for k in REQUIRED_COOKIE_KEYS if not str(cookies.get(k, "")).strip()]
    if missing:
        raise CookieError(CookieError.MISSING_KEYS.format(keys=", ".join(missing)))
    return cookies


# Ties the returned member to the enum passed in, so a caller gets ``ApiProvider`` back, not a bare ``Enum``.
E = TypeVar("E", bound=Enum)


def parse_enum(enum: type[E], raw: str, error: str) -> E:
    """The member of ``enum`` whose value is ``raw``, ignoring case and surrounding spaces."""
    members = {str(member.value).lower(): member for member in enum}
    try:
        return members[raw.strip().lower()]
    except KeyError:
        supported = ", ".join(sorted(str(member.value) for member in enum))
        raise ConfigurationError(error.format(value=raw, supported=supported)) from None


def normalize_mnemonic_type(mnemonic_type: str | None, wallet_version: WalletVersion) -> MnemonicType:
    """The phrase scheme to derive the key with: TON by default, multichain for a Telegram Wallet."""
    if mnemonic_type is None:
        return MnemonicType.MULTICHAIN if wallet_version == WalletVersion.TG else MnemonicType.TON
    return parse_enum(MnemonicType, mnemonic_type, ConfigurationError.UNSUPPORTED_MNEMONIC_TYPE)


def normalize_gift_attributes(attr: Mapping[str, Sequence[str]] | None) -> dict[GiftAttribute, list[str]]:
    return {
        parse_enum(GiftAttribute, name, ConfigurationError.INVALID_GIFT_ATTRIBUTE): list(values)
        for name, values in (attr or {}).items()
    }


def check_limit(bounds: Range, value: object) -> None:
    # bool is a subclass of int, but `True` is never a meaningful amount or count.
    if not isinstance(value, int) or isinstance(value, bool) or not bounds.min <= value <= bounds.max:
        raise ConfigurationError(ConfigurationError.OUT_OF_RANGE.format(label=bounds.label, min=bounds.min, max=bounds.max))


def check_stars_winners(winners: int, amount: int) -> None:
    """A Stars giveaway package is split between its winners, each getting at least a fixed share."""
    most = amount // STARS_GIVEAWAY_MIN_PER_WINNER
    if winners > most:
        raise ConfigurationError(
            ConfigurationError.TOO_MANY_WINNERS.format(amount=amount, max=most, per_winner=STARS_GIVEAWAY_MIN_PER_WINNER)
        )


def check_months(months: object) -> None:
    if not isinstance(months, int) or isinstance(months, bool) or months not in PREMIUM_MONTHS_VALID:
        raise ConfigurationError(ConfigurationError.INVALID_MONTHS)


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
    if payment_method not in set(PaymentMethod):
        supported = ", ".join(PaymentMethod)
        raise ConfigurationError(ConfigurationError.INVALID_PAYMENT_METHOD.format(method=payment_method, supported=supported))
