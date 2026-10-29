from __future__ import annotations

from decimal import ROUND_CEILING, Decimal, InvalidOperation


def to_units(amount: Decimal, decimals: int) -> int:
    """Smallest units of ``amount``, rounded up: an amount that has to be paid is never underestimated."""
    return int((amount.scaleb(decimals)).to_integral_value(rounding=ROUND_CEILING))


def from_units(units: int, decimals: int) -> Decimal:
    """Exact ``Decimal`` value of ``units`` smallest units."""
    return Decimal(units).scaleb(-decimals).quantize(Decimal(1).scaleb(-decimals))


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
