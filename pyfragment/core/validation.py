from __future__ import annotations

import json
from typing import Any, cast

from pyfragment.core.constants import MNEMONIC_WORD_COUNTS_VALID, REQUIRED_COOKIE_KEYS
from pyfragment.enums import ApiProvider, WalletVersion
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
    version = wallet_version.strip().upper()
    try:
        return WalletVersion(version)
    except ValueError:
        raise ConfigurationError(
            ConfigurationError.UNSUPPORTED_VERSION.format(
                version=version,
                supported=", ".join(sorted(m.value for m in WalletVersion)),
            )
        )


def validate_credentials(seed: str, api_key: str) -> None:
    missing = [name for name, val in (("seed", seed), ("api_key", api_key)) if not val or not str(val).strip()]
    if missing:
        raise ConfigurationError(ConfigurationError.MISSING_VARS.format(keys=", ".join(missing)))

    word_count = len(seed.split())
    if word_count not in MNEMONIC_WORD_COUNTS_VALID:
        raise ConfigurationError(ConfigurationError.INVALID_MNEMONIC.format(count=word_count))
