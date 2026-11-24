from __future__ import annotations

from typing import NamedTuple


class Range(NamedTuple):
    """Inclusive bounds of an amount or a count Fragment accepts."""

    label: str
    min: int
    max: int


STARS_PURCHASE = Range("Stars amount", 50, 10_000_000)
# A package is split between the winners, each getting at least STARS_GIVEAWAY_MIN_PER_WINNER.
STARS_GIVEAWAY = Range("Stars package", 500, 1_000_000)
STARS_GIVEAWAY_MIN_PER_WINNER = 100
STARS_WINNERS = Range("winners count", 1, 10_000)
PREMIUM_WINNERS = Range("winners count", 1, 24_000)

# Premium subscription durations (months)
PREMIUM_MONTHS_VALID: frozenset[int] = frozenset({3, 6, 12})
