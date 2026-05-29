from __future__ import annotations

# Stars: direct purchase
STARS_PURCHASE_MIN: int = 50
STARS_PURCHASE_MAX: int = 10_000_000

# Stars: giveaway per winner
STARS_GIVEAWAY_MIN: int = 500
STARS_GIVEAWAY_MAX: int = 1_000_000

# Stars giveaway winners count
STARS_WINNERS_MIN: int = 1
STARS_WINNERS_MAX: int = 15

# Premium giveaway winners count
PREMIUM_WINNERS_MIN: int = 1
PREMIUM_WINNERS_MAX: int = 24_000

# TON topup / Ads recharge amount
TON_TOPUP_MIN: int = 1
TON_TOPUP_MAX: int = 1_000_000_000

# Wallet minimum balances
MIN_TON_BALANCE: float = 0.33
MIN_USDT_BALANCE: float = 0.75

# Premium subscription durations (months)
PREMIUM_MONTHS_VALID: frozenset[int] = frozenset({3, 6, 12})

# Mnemonic phrase valid word counts
MNEMONIC_WORD_COUNTS_VALID: frozenset[int] = frozenset({12, 24})

# Tonapi API key minimum length
TONAPI_KEY_MIN_LENGTH: int = 68
