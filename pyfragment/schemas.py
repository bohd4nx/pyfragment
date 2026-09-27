"""Typed views of the JSON bodies Fragment's ``/api`` endpoint returns."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pyfragment.enums import ApiError, StateMode


def error_text(response: dict[str, Any]) -> str | None:
    """The ``error`` message of a response, or ``None`` when the call succeeded."""
    error = response.get("error")
    return str(error) if error else None


def has_error(response: dict[str, Any], error: ApiError) -> bool:
    """Whether the response's error text contains a known Fragment error message."""
    text = error_text(response)
    return text is not None and error.casefold() in text.casefold()


@dataclass(frozen=True)
class RecipientSearch:
    """Result of a ``search*Recipient`` call."""

    recipient: str | None

    @classmethod
    def from_response(cls, response: dict[str, Any]) -> RecipientSearch:
        found = response.get("found")
        recipient = found.get("recipient") if isinstance(found, dict) else None
        return cls(recipient=recipient or None)


@dataclass(frozen=True)
class InvoiceRequest:
    """Result of an ``init*Request`` call: the invoice id and the amount Fragment expects to be paid."""

    req_id: str | None
    amount: float | None

    @classmethod
    def from_response(cls, response: dict[str, Any]) -> InvoiceRequest:
        return cls(req_id=response.get("req_id") or None, amount=_parse_amount(response.get("amount")))


@dataclass(frozen=True)
class TransactionLink:
    """Result of a ``get*Link`` call: the transaction to sign plus how to report it back."""

    need_verify: bool
    confirm_method: str | None
    confirm_params: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_response(cls, response: dict[str, Any]) -> TransactionLink:
        return cls(
            need_verify=bool(response.get("need_verify")),
            confirm_method=response.get("confirm_method") or None,
            confirm_params=response.get("confirm_params") or {},
        )


@dataclass(frozen=True)
class PageState:
    """Result of an ``update*State`` poll: Fragment's view of where the purchase stands."""

    mode: str
    need_update: bool

    @classmethod
    def from_response(cls, response: dict[str, Any], default_mode: str = StateMode.NEW) -> PageState:
        return cls(mode=str(response.get("mode", default_mode)), need_update=bool(response.get("need_update", True)))

    @property
    def is_done(self) -> bool:
        """Fragment's definitive signal that it has processed the transaction."""
        return not self.need_update


def _parse_amount(raw_amount: object) -> float | None:
    try:
        # Fragment formats larger amounts with thousand separators (e.g. "1,000,000,000").
        return float(str(raw_amount).replace(",", ""))
    except (TypeError, ValueError):
        return None
