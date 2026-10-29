from __future__ import annotations

import html
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from pyfragment.enums import ApiError, StateMode
from pyfragment.utils.money import parse_amount


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
    name: str | None = None
    photo: str | None = None  # an HTML <img> tag, as Fragment renders it
    myself: bool = False

    @classmethod
    def from_response(cls, response: dict[str, Any]) -> RecipientSearch:
        found = response.get("found")
        if not isinstance(found, dict):
            return cls(recipient=None)
        name = found.get("name")
        return cls(
            recipient=found.get("recipient") or None,
            # Fragment HTML-escapes the display name (its frontend unescapes it before showing it).
            name=html.unescape(str(name)) if name else None,
            photo=found.get("photo") or None,
            myself=bool(found.get("myself")),
        )


@dataclass(frozen=True)
class InvoiceRequest:
    """Result of an ``init*Request`` call: the invoice id and the amount Fragment expects to be paid."""

    req_id: str | None
    amount: Decimal | None  # in the payment currency: GRAM (ex TON) or USDT

    @classmethod
    def from_response(cls, response: dict[str, Any]) -> InvoiceRequest:
        return cls(req_id=response.get("req_id") or None, amount=parse_amount(response.get("amount")))


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
