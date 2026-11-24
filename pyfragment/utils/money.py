from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation


def parse_amount(raw: object) -> Decimal | None:
    """A non-negative amount as Fragment formats it (``"0.4609"``, ``"1,000,000"``), or ``None``."""
    if isinstance(raw, bool) or raw is None:
        return None
    try:
        # Fragment formats larger amounts with thousand separators (e.g. "1,000,000,000").
        amount = Decimal(str(raw).replace(",", "").strip())
    except InvalidOperation:
        return None
    return amount if amount.is_finite() and amount >= 0 else None


def numbers_in(text: str) -> list[int]:
    """The whole numbers of Fragment's message, thousands separators dropped: ``"up to 10,000,000"`` -> ``[10000000]``."""
    return [int(number.replace(",", "")) for number in re.findall(r"\d[\d,]*", text)]
