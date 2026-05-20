from __future__ import annotations

from typing import Any


def parse_required_payment_amount(init_response: dict[str, Any]) -> float | None:
    raw_amount = init_response.get("amount")
    try:
        return float(str(raw_amount))
    except (TypeError, ValueError):
        return None
