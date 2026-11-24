from __future__ import annotations

from typing import NamedTuple


class Range(NamedTuple):
    """Inclusive bounds of an amount or a count Fragment accepts."""

    label: str
    min: int
    max: int


STARS_PURCHASE = Range("Stars amount", 50, 10_000_000)
# The package is shared by the winners and each gets at least STARS_GIVEAWAY_MIN_PER_WINNER, so a package of
# N Stars allows N // STARS_GIVEAWAY_MIN_PER_WINNER winners (STARS_WINNERS.max is that for the largest package).
STARS_GIVEAWAY = Range("Stars package", 500, 1_000_000)
STARS_GIVEAWAY_MIN_PER_WINNER = 100
STARS_WINNERS = Range("winners count", 1, 10_000)
PREMIUM_WINNERS = Range("winners count", 1, 24_000)

# Premium subscription durations (months)
PREMIUM_MONTHS_VALID: frozenset[int] = frozenset({3, 6, 12})
