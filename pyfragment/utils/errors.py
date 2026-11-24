from __future__ import annotations

import html
from collections.abc import Callable
from typing import Any

from pyfragment.enums import ApiError
from pyfragment.exceptions import (
    AboveMaximumError,
    AmountError,
    BelowMinimumError,
    FragmentAPIError,
    InvalidPackageError,
)

# Messages that mean the same wherever Fragment sends them. Those that depend on the call
# (an expired invoice, an already linked wallet) are told apart where the call is made.
TYPED_ERRORS: dict[ApiError, Callable[[str], FragmentAPIError]] = {
    ApiError.BELOW_MINIMUM: BelowMinimumError.from_text,
    ApiError.ABOVE_MAXIMUM_BUY: AboveMaximumError.from_text,
    ApiError.ABOVE_MAXIMUM_CHOOSE: AboveMaximumError.from_text,
    ApiError.AMOUNT_RANGE: AmountError.from_text,
    ApiError.INVALID_PACKAGE: InvalidPackageError,
}


def error_text(response: dict[str, Any]) -> str | None:
    """Fragment's error message; it HTML-escapes it because its frontend puts it into a page."""
    error = response.get("error")
    return html.unescape(str(error)) if error else None


def has_error(response: dict[str, Any], error: ApiError) -> bool:
    """Whether the response's error text contains a known Fragment error message."""
    text = error_text(response)
    return text is not None and error.casefold() in text.casefold()


def api_error(response: dict[str, Any]) -> FragmentAPIError | None:
    """The exception for the response's error text (a specific one for known messages), or None without an error."""
    if (text := error_text(response)) is None:
        return None
    for known, build in TYPED_ERRORS.items():
        if has_error(response, known):
            return build(text)
    return FragmentAPIError(text)


def raise_for_error(response: dict[str, Any]) -> None:
    if (error := api_error(response)) is not None:
        raise error
